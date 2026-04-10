# Единая система аварийного мониторинга

Файл: `Code/emergency_system.py`

Модели расположены в: `Code/models`  
Дополнительные README-материалы: `Code/RM`

Программа принимает пакет показаний датчиков и параллельно запускает 4 проверки:

1. `detect_flood` (флаг наводнения/затопления, ML-интерфейс + fallback на threshold)
2. `detect_fire` (флаг пожара, ML-модель `models/smoke_model.pkl`)
3. `detect_gas_leak` (флаг утечки газа, кумулянтный метод + fallback ML/threshold)
4. `detect_intrusion_alarm` (флаг вторжения)

На выходе формируется вектор из 4 позиций:

`[flood_alarm, fire_alarm, gas_leak_alarm, intrusion_alarm]`

- `1` — авария
- `0` — всё в норме

## Формат входных данных

Поддерживаются два формата элемента:

- список/кортеж: `[sensor_type, sensor_id, room, reading]`
- словарь: `{ "sensor_type": ..., "sensor_id": ..., "room": ..., "reading": ... }`

Пример пакета:

```json
[
  ["flood", 1, 101, 0.95],
  ["fire", 2, 101, 0.20],
  ["leak", 3, 102, 0.80],
  ["door_break", 4, 101, 1]
]
```

## Запуск

```bash
cd Code
pip install -r requirements.txt
python3 emergency_system.py << 'JSON'
[
  ["flood", 1, 101, 0.95],
  ["fire", 2, 101, 0.20],
  ["leak", 3, 102, 0.80],
  ["door_break", 4, 101, 1]
]
JSON
```

Пример вывода:

```json
[1, 0, 1, 1]
```

## Генератор тестовых пакетов (0/1)

Файл: `Code/test/generate_sensor_batch.py`

- `1` — генерирует пакет, который должен вызывать срабатывание системы.
- `0` — генерирует пакет, который не должен вызывать срабатывание.
- seed берётся из количества секунд Unix-time: `int(time.time())`.

Примеры:

```bash
cd Code
python3 test/generate_sensor_batch.py 1
python3 test/generate_sensor_batch.py 0
python3 test/generate_sensor_batch.py 1 --source safe --with-meta
python3 test/generate_sensor_batch.py 0 --source full --with-meta
```

С метаданными (seed + цель):

```bash
python3 test/generate_sensor_batch.py 1 --with-meta
```

Проверка в пайплайне:

```bash
python3 test/generate_sensor_batch.py 1 | python3 emergency_system.py
python3 test/generate_sensor_batch.py 0 | python3 emergency_system.py
```

## Тестовый скрипт

Файл: `Code/test/run_emergency_tests.py`

```bash
cd Code
python3 test/run_emergency_tests.py --dataset safe --limit 200
python3 test/run_emergency_tests.py --dataset full --limit 1000
```

Скрипт:
- запускает `emergency_system.py` как основную программу;
- проверяет synthetic-генератор;
- проверяет сценарий проникновения (квартира: гостиная/спальня/коридор/кухня, 2 motion-датчика в каждой комнате + входная дверь);
- проверяет сценарий утечки газа;
- проверяет корректность dataset-режима генератора (4 сценария: gas/intrusion без fallback, safe-dataset fallback, отсутствие fire FP при gas-only);
- проверяет датасеты `safe_unified_test_clean.csv` и `unified_test_clean.csv`.

## Анализ диапазонов аварийных значений (ML calibration)

Файл: `Code/utilites/analyze_dataset_alarm_ranges.py`

Скрипт проходит по датасетам и для каждой метки тревоги (`smoke_label=1`, `leak_label=1`) выводит диапазоны (min/max/percentiles) по всем числовым признакам. Используется для калибровки ML-порогов и синтетических alarm-смещений.

```bash
cd Code
# Stdout-таблица по обоим датасетам
python3 utilites/analyze_dataset_alarm_ranges.py

# Сохранить в CSV
python3 utilites/analyze_dataset_alarm_ranges.py --output csv --out-file alarm_ranges.csv

# Сохранить в JSON
python3 utilites/analyze_dataset_alarm_ranges.py --output json --out-file alarm_ranges.json

# Анализ конкретного файла и метки
python3 utilites/analyze_dataset_alarm_ranges.py \
    --dataset test/unified_test_clean.csv \
    --label smoke_label
```

## Qt GUI генератор

Файл: `Code/test/qt_sensor_generator.py`

```bash
cd Code
python3 test/qt_sensor_generator.py
```

GUI умеет:
- работать в потоковом режиме (`Старт`/`Стоп`) с постоянным обновлением данных и кнопкой `Обнулить`;
- сдвигать окрестность в alarm-зону по 4 галочкам: `Пожар`, `Затопление`, `Утечка газа`, `Проникновение`;
- брать seed автоматически как текущее время в секундах через `time.time()` (поле seed в GUI скрыто);
- в режиме `safe/full` подтягивать строки датасета по доступной метке `smoke_label`; для недоступных меток (flood/gas/intrusion) может использоваться synthetic fallback;
- показывать в интерфейсе подтверждение чтения CSV (`источник`, `индекс строки`, `путь файла`);
- брать параметры генерации/смещений из `Code/test/qt_sensor_generator_config.json` в **SI**;
- показывать confusion-таблицу (True/False Positive/Negative) по 4 детекторам и сохранять JSON-пакет.

### Правила генерации в dataset-режиме (`safe`/`full`)

Контракт подсистем задаёт три независимых источника данных в одном пакете:

| Подсистема | Метод обнаружения | Источник значений в dataset-режиме |
|---|---|---|
| **Пожар** | ML-модель (`smoke_model.pkl`) | Строка датасета (колонки fire-сенсоров, выбор по `smoke_label`) |
| **Затопление** | ML-модель | Синтетическая генерация (нет колонки `flood` в CSV) |
| **Утечка газа** | Кумулянтный метод | **Всегда синтетическая** (независимо от режима) |
| **Проникновение** | Rule-based (`intrusion_detection.py`) | **Всегда синтетическая** (независимо от режима) |

Правила:
- Выбор строки из датасета осуществляется **только** по метке пожара (`smoke_label`): gas/flood/intrusion-галочки не влияют на выбор строки.
- Из датасетной строки берутся только **fire-сенсоры** (`temp_ambient_c`, `humidity_pct`, `tvoc_ppb` и т.д.).
- Газовые сенсоры (`gas_leak`, `press_pipe_bar`, `flow_rate_lps`, `temp_pipe_c`) и датчики проникновения (`door_break`, `ir_motion`) **всегда генерируются синтетически** на основе соответствующих галочек.
- Датчик затопления (`flood`) также всегда синтетический (отсутствует в датасетах).
- Если в датасете нет строк с нужной меткой пожара (например, `fire=True` в `safe`-датасете, а там нет `smoke_label=0`), включается **synthetic fallback** только для fire-сенсоров; gas/flood/intrusion остаются синтетическими в любом случае.
- В таблице GUI ожидания (`expected`) для всех 4 детекторов теперь всегда берутся из выбранного профиля галочек (0/1), независимо от источника данных.
- Для снижения ложных перекрёстных срабатываний при переключении профилей используется изоляция по `room_id` (история ML/кумулянтов отделяется между разными наборами галочек), а генератор делает несколько попыток подбора батча к целевому вектору 0/1.

Если на Windows возникает ошибка про `QT platform plugin`:
- запускайте скрипт из venv с установленным `PyQt5`;
- скрипт теперь сам пытается выставить корректные `QT_QPA_PLATFORM_PLUGIN_PATH`/`QT_PLUGIN_PATH` для PyQt5;
- если переменные среды указывают на несуществующий Qt-путь, удалите их и запустите снова.

## Номенклатура датчиков

Всего в текущей системе используется **18 видов датчиков**:
- **15 видов из `unified_test_clean.csv`** (температура, влажность, TVOC, eCO2, пыль, давление/поток в трубе и т.д.);
- **3 intrusion-типа**: `ir_motion`, `door_break`, `window_open`.

### Логические типы датчиков в оркестраторе

- **Наводнение/затопление**: `flood`, `water_level`, `waterlevel`, `rain`, `drain`, код `300`
- **Пожар/дым**: `fire`, `smoke`, `temperature`, `temp`, `co2`, `tvoc`, `eco2`, код `100`, а также поля `temp_ambient_c`, `humidity_pct`, `tvoc_ppb`, `eco2_ppm`, `raw_h2`, `raw_ethanol`, `press_ambient_bar`, `pm1_0`, `pm2_5`, `nc0_5`, `nc1_0`, `nc2_5`
- **Утечка газа**: `gas_leak`, `leak`, `water_leak` (алиас), `tvoc_ppb`, `eco2_ppm`, `raw_h2`, `raw_ethanol`, `press_pipe_bar`, `flow_rate_lps`, `temp_pipe_c`
- **Вторжение**: `ir_motion` (0), `door_break` (1), `window_open` (2), а также числовые `0/1/2`

### Поля тестового датасета (дым + инженерные сенсоры)

- `index`
- `timestamp`
- `temp_ambient_c`
- `humidity_pct`
- `tvoc_ppb`
- `eco2_ppm`
- `raw_h2`
- `raw_ethanol`
- `press_ambient_bar`
- `pm1_0`
- `pm2_5`
- `nc0_5`
- `nc1_0`
- `nc2_5`
- `smoke_label`
- `press_pipe_bar`
- `flow_rate_lps`
- `temp_pipe_c`
- `leak_label`

Связь полей и подсистем:

- **Пожар/дым (`fire_test`)**:  
  `temp_ambient_c`, `humidity_pct`, `tvoc_ppb`, `eco2_ppm`, `raw_h2`, `raw_ethanol`, `press_ambient_bar`, `pm1_0`, `pm2_5`, `nc0_5`, `nc1_0`, `nc2_5`, целевая метка `smoke_label`.
- **Утечка газа (`detect_gas_leak`)**:  
  кумулянты 2..6 по истории газового сигнала; при недостатке истории возвращается 0, далее fallback на ML/threshold.
- **Наводнение (`detect_flood_threshold`)**:  
  используется потоковый показатель уровня/факта воды в `reading` (в оркестраторе), без привязки к фиксированному CSV-столбцу.
- **Вторжение (`intrusion_detection`)**:  
  используется тип датчика вторжения + идентификатор + комната + факт срабатывания (`reading > 0`).

## Замечания

- Выполнение 4 подсистем происходит параллельно через `ThreadPoolExecutor`.
- Для `detect_fire` и `detect_flood` используется ML-инференс с rolling-window агрегацией (`window_size=5`) по in-memory истории последних пакетов на комнату.
- Внешний контракт `process_sensor_batch` принимает **физические значения в SI** (за исключением оговорённых сенсоров концентраций и flood-уровня):
  - `temp_ambient_c`, `temp_pipe_c`: **K** (Кельвины)
  - `humidity_pct`: **доля 0..1**
  - `press_ambient_bar`, `press_pipe_bar`: **Pa**
  - `flow_rate_lps`: **м³/с**
  - `tvoc_ppb`: **ppb**, `eco2_ppm`: **ppm** (как исходные сенсоры)
  - `pm1_0`, `pm2_5`, `nc*`: как в датасете
  - `flood`: нормализованный `flood_level_norm` в диапазоне `0..1`
- Перед ML-инференсом значения автоматически приводятся к единицам, в которых обучались модели:
  - fire-модель: `Temperature[C]`, `Humidity[%]`, `Pressure[hPa]` и т.д.
- Если `joblib`/`pandas`/`scikit-learn` недоступны или `.pkl` отсутствует, для fire/flood включается fallback на пороги.
- В датасетах для текущей оценки используется только `smoke_label`; для flood/gas/intrusion отсутствуют валидные ground-truth метки, поэтому их dataset-метрики в GUI/скриптах помечаются как недоступные.
- При несовпадении версий sklearn для `.pkl` выводится одно агрегированное предупреждение (один раз), с рекомендацией установить `scikit-learn==1.8.0`.
- Для подсистемы intrusion используются правила из `intrusion_detection.py`.
- Для intrusion учитываются только сработавшие датчики (`reading > 0`).
- Поддерживаемые intrusion-типы: `ir_motion`, `door_break`, `window_open` и числовые `0/1/2`.
