# Единая система аварийного мониторинга

Файл: `Code/emergency_system.py`

Модели расположены в: `Code/models`  
Дополнительные README-материалы: `Code/RM`

Программа принимает пакет показаний датчиков и параллельно запускает 4 проверки:

1. `detect_flood_threshold` (флаг наводнения/затопления)
2. `detect_fire` (флаг пожара)
3. `detect_water_leak` (флаг утечки воды)
4. `detect_intrusion_alarm` (флаг вторжения)

На выходе формируется вектор из 4 позиций:

`[flood_alarm, fire_alarm, leak_alarm, intrusion_alarm]`

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
- проверяет сценарий утечки газа (рост `tvoc_ppb`/`eco2_ppm`/`smoke`);
- проверяет датасеты `safe_unified_test_clean.csv` и `unified_test_clean.csv`.

## Qt GUI генератор

Файл: `Code/test/qt_sensor_generator.py`

```bash
cd Code
python3 test/qt_sensor_generator.py
```

GUI умеет:
- работать в потоковом режиме (`Старт`/`Стоп`) с постоянным обновлением данных и кнопкой `Обнулить`;
- сдвигать окрестность в alarm-зону по 4 галочкам: `Пожар`, `Затопление`, `Утечка Газа`, `Проникновение`;
- брать seed автоматически как текущее время в секундах через `time.time()` (поле seed в GUI скрыто);
- в режиме `safe/full` подтягивать строки датасета под выбранные сработки (`smoke_label`/`leak_label`);
- показывать в интерфейсе подтверждение чтения CSV (`источник`, `индекс строки`, `путь файла`);
- брать параметры окрестности из `Code/test/qt_sensor_generator_config.json`;
- показывать confusion-таблицу (True/False Positive/Negative) по 4 детекторам и сохранять JSON-пакет.

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
- **Утечка воды**: `leak`, `water_leak`, `pipe_pressure`, `flow`, `flow_rate`, код `200`, а также `press_pipe_bar`, `flow_rate_lps`, `temp_pipe_c`
- **Вторжение**: `ir_motion` (0), `door_break` (1), `window_open` (2), а также числовые `0/1/2`

### Поля тестового датасета (дым/затопление/утечка)

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
- **Утечка воды (`water_test`)**:  
  `press_pipe_bar`, `flow_rate_lps`, `temp_pipe_c`, целевая метка `leak_label`.
- **Наводнение (`detect_flood_threshold`)**:  
  используется потоковый показатель уровня/факта воды в `reading` (в оркестраторе), без привязки к фиксированному CSV-столбцу.
- **Вторжение (`intrusion_detection`)**:  
  используется тип датчика вторжения + идентификатор + комната + факт срабатывания (`reading > 0`).

## Замечания

- Выполнение 4 подсистем происходит параллельно через `ThreadPoolExecutor`.
- Для подсистемы intrusion используются правила из `intrusion_detection.py`.
- Для intrusion учитываются только сработавшие датчики (`reading > 0`).
- Поддерживаемые intrusion-типы: `ir_motion`, `door_break`, `window_open` и числовые `0/1/2`.
