from __future__ import annotations

import csv
import json
import os
import random
import sys
import time
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Tuple

from generate_sensor_batch import (
    DEFAULT_ROOM_ID,
    SAFE_DATASET_PATH,
    UNIFIED_DATASET_PATH,
    dataframe_row_to_batch,
)

CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
from emergency_system import process_sensor_batch  # type: ignore[import-not-found]

CONFIG_PATH = CURRENT_DIR / "qt_sensor_generator_config.json"
DEFAULT_CONFIG: Dict[str, Dict[str, float]] = {
    "neighborhood": {
        "radius": 0.04,
        "safe_center": 0.25,
        "fire_center": 0.9,
        "leak_center": 0.88,
        "flood_center": 0.98,
    },
    "stream": {"interval_ms": 5000.0},
}

FIRE_SENSOR_TYPES = {
    "smoke",
    "temp_ambient_c",
    "tvoc_ppb",
    "eco2_ppm",
    "raw_h2",
    "raw_ethanol",
    "press_ambient_bar",
    "pm1_0",
    "pm2_5",
    "nc0_5",
    "nc1_0",
    "nc2_5",
}
LEAK_SENSOR_TYPES = {"leak", "press_pipe_bar", "flow_rate_lps", "temp_pipe_c"}
FLOOD_SENSOR_TYPES = {"flood"}
DETECTOR_LABELS = ["Затопление", "Пожар", "Утечка Газа", "Проникновение"]
METRICS_ROW_ORDER = ["TP", "FP", "TN", "FN"]
SOURCE_OPTIONS: List[Mapping[str, str]] = [
    {"label": "Синтетический", "key": "synthetic"},
    {"label": "Безопасный датасет", "key": "safe"},
    {"label": "Полный датасет", "key": "full"},
]
ALARM_NAME_BY_KEY = {
    "fire": "Пожар",
    "flood": "Затопление",
    "gas_leak": "Утечка Газа",
    "intrusion": "Проникновение",
}
NEIGHBORHOOD_SEED_OFFSET = 19
FLOOD_SEED_OFFSET = 99
MINIMUM_ALLOWED_STREAM_INTERVAL_MS = 100


def _prepare_qt_environment() -> None:
    if not sys.platform.startswith("win"):
        return

    os.environ.setdefault("QT_QPA_PLATFORM", "windows")
    plugin_paths: List[Path] = []

    try:
        import PyQt5  # type: ignore[import-not-found]

        pyqt_dir = Path(PyQt5.__file__).resolve().parent
        plugin_paths.extend([pyqt_dir / "Qt5" / "plugins", pyqt_dir / "Qt" / "plugins"])
    except Exception:
        pass

    try:
        from PyQt5.QtCore import QLibraryInfo  # type: ignore[import-not-found]

        plugins_path = QLibraryInfo.location(QLibraryInfo.PluginsPath)
        if plugins_path:
            plugin_paths.append(Path(plugins_path))
    except Exception:
        pass

    valid_plugins = [p for p in plugin_paths if (p / "platforms").exists()]
    if not valid_plugins:
        return

    plugins_dir = valid_plugins[0]
    platforms_dir = plugins_dir / "platforms"
    if not os.environ.get("QT_QPA_PLATFORM_PLUGIN_PATH"):
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(platforms_dir)
    if not os.environ.get("QT_PLUGIN_PATH"):
        os.environ["QT_PLUGIN_PATH"] = str(plugins_dir)


def _load_config() -> Dict[str, Dict[str, float]]:
    config = json.loads(json.dumps(DEFAULT_CONFIG))
    if not CONFIG_PATH.exists():
        return config
    try:
        loaded = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return config
    neighborhood = loaded.get("neighborhood", {})
    if isinstance(neighborhood, dict):
        for key in ("radius", "safe_center", "fire_center", "leak_center", "flood_center"):
            value = neighborhood.get(key)
            if isinstance(value, (int, float)):
                config["neighborhood"][key] = float(value)
    stream = loaded.get("stream", {})
    if isinstance(stream, dict):
        value = stream.get("interval_ms")
        if isinstance(value, (int, float)) and value >= MINIMUM_ALLOWED_STREAM_INTERVAL_MS:
            config["stream"]["interval_ms"] = float(value)
    return config


def _clip01(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 4)


def _jitter(rng: random.Random, center: float, radius: float) -> float:
    return _clip01(rng.uniform(center - radius, center + radius))


def _alarm_centers(config: Mapping[str, Mapping[str, float]], profile: Mapping[str, bool]) -> Dict[str, float]:
    n = config["neighborhood"]
    safe_center = float(n["safe_center"])
    return {
        "fire": float(n["fire_center"]) if profile["fire"] else safe_center,
        "gas_leak": float(n["leak_center"]) if profile["gas_leak"] else safe_center,
        "flood": float(n["flood_center"]) if profile["flood"] else safe_center,
    }


def _synthetic_batch(
    profile: Mapping[str, bool],
    config: Mapping[str, Mapping[str, float]],
    seed: int,
) -> List[List[object]]:
    rng = random.Random(seed)
    radius = float(config["neighborhood"]["radius"])
    centers = _alarm_centers(config=config, profile=profile)
    intrusion_value = 1.0 if profile["intrusion"] else 0.0
    room = DEFAULT_ROOM_ID

    return [
        ["flood", 3001, room, _jitter(rng, centers["flood"], radius)],
        ["smoke", 1001, room, _jitter(rng, centers["fire"], radius)],
        ["leak", 2001, room, _jitter(rng, centers["gas_leak"], radius)],
        ["temp_ambient_c", 1101, room, _jitter(rng, centers["fire"], radius)],
        ["tvoc_ppb", 1102, room, _jitter(rng, centers["fire"], radius)],
        ["eco2_ppm", 1103, room, _jitter(rng, centers["fire"], radius)],
        ["flow_rate_lps", 2101, room, _jitter(rng, centers["gas_leak"], radius)],
        ["press_pipe_bar", 2102, room, _jitter(rng, centers["gas_leak"], radius)],
        ["door_break", 1, room, intrusion_value],
        ["ir_motion", 2, room, intrusion_value],
    ]


def _dataset_path(source: str) -> Path:
    if source == "safe":
        return SAFE_DATASET_PATH
    if source == "full":
        return UNIFIED_DATASET_PATH
    raise ValueError("source must be safe/full for dataset mode")


def _row_matches_profile(row: Mapping[str, str], profile: Mapping[str, bool]) -> bool:
    smoke_active = int(float(row.get("smoke_label", "0"))) == 1
    leak_active = int(float(row.get("leak_label", "0"))) == 1
    any_alarm_checked = any(profile.values())
    # Datasets include only smoke/leak labels; flood/intrusion values are generated in batch.

    if profile["fire"] and not smoke_active:
        return False
    if profile["gas_leak"] and not leak_active:
        return False
    if not any_alarm_checked and (smoke_active or leak_active):
        return False
    return True


def _pick_dataset_row(source: str, profile: Mapping[str, bool], seed: int) -> Tuple[MutableMapping[str, str], int]:
    path = _dataset_path(source)
    with path.open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))

    matching: List[Tuple[int, MutableMapping[str, str]]] = [
        (idx, row) for idx, row in enumerate(rows) if _row_matches_profile(row, profile)
    ]
    if not matching:
        active = [name for key, name in ALARM_NAME_BY_KEY.items() if profile[key]]
        active_text = ", ".join(active) if active else "без сработок"
        raise ValueError(f'Нет строк датасета "{source}" под профиль: {active_text}.')
    rng = random.Random(seed)
    selected_idx, selected_row = matching[rng.randrange(len(matching))]
    return selected_row, selected_idx


def _adjust_batch_neighborhood(
    batch: Iterable[List[object]],
    profile: Mapping[str, bool],
    config: Mapping[str, Mapping[str, float]],
    seed: int,
) -> List[List[object]]:
    rng = random.Random(seed + NEIGHBORHOOD_SEED_OFFSET)
    radius = float(config["neighborhood"]["radius"])
    centers = _alarm_centers(config=config, profile=profile)
    adjusted: List[List[object]] = []
    for sensor_type, sensor_id, room, reading in batch:
        st = str(sensor_type).lower()
        center = float(reading)
        if st in FIRE_SENSOR_TYPES:
            center = centers["fire"]
        elif st in LEAK_SENSOR_TYPES:
            center = centers["gas_leak"]
        elif st in FLOOD_SENSOR_TYPES:
            center = centers["flood"]
        adjusted.append([sensor_type, sensor_id, room, _jitter(rng, center, radius)])
    return adjusted


def _calc_confusion(expected: int, predicted: int) -> Dict[str, int]:
    return {
        "TP": int(expected == 1 and predicted == 1),
        "FP": int(expected == 0 and predicted == 1),
        "TN": int(expected == 0 and predicted == 0),
        "FN": int(expected == 1 and predicted == 0),
    }


def generate_profiled_batch(
    source: str,
    profile: Mapping[str, bool],
    seed: int,
    config: Mapping[str, Mapping[str, float]],
) -> Dict[str, object]:
    dataset_path = None
    if source == "synthetic":
        batch = _synthetic_batch(profile=profile, config=config, seed=seed)
        selected_row_index = None
    else:
        dataset_path = str(_dataset_path(source))
        row, selected_row_index = _pick_dataset_row(source=source, profile=profile, seed=seed)
        batch = dataframe_row_to_batch(row)
        batch = _adjust_batch_neighborhood(batch=batch, profile=profile, config=config, seed=seed)
        intrusion_value = 1.0 if profile["intrusion"] else 0.0
        batch.extend(
            [
                ["door_break", 1, DEFAULT_ROOM_ID, intrusion_value],
                ["ir_motion", 2, DEFAULT_ROOM_ID, intrusion_value],
            ]
        )
        if "flood" not in {str(item[0]).lower() for item in batch}:
            radius = float(config["neighborhood"]["radius"])
            center = _alarm_centers(config=config, profile=profile)["flood"]
            batch.append(
                ["flood", 3001, DEFAULT_ROOM_ID, _jitter(random.Random(seed + FLOOD_SEED_OFFSET), center, radius)]
            )

    predicted = process_sensor_batch(batch)
    expected = {
        "Затопление": int(profile["flood"]),
        "Пожар": int(profile["fire"]),
        "Утечка Газа": int(profile["gas_leak"]),
        "Проникновение": int(profile["intrusion"]),
    }
    confusion = {
        "Затопление": _calc_confusion(expected["Затопление"], int(predicted[0])),
        "Пожар": _calc_confusion(expected["Пожар"], int(predicted[1])),
        "Утечка Газа": _calc_confusion(expected["Утечка Газа"], int(predicted[2])),
        "Проникновение": _calc_confusion(expected["Проникновение"], int(predicted[3])),
    }

    return {
        "seed": seed,
        "source": source,
        "dataset_path": dataset_path,
        "config_path": str(CONFIG_PATH),
        "radius": config["neighborhood"]["radius"],
        "profile": dict(profile),
        "selected_dataset_row_index": selected_row_index,
        "sensor_types_count": len({item[0] for item in batch}),
        "expected": expected,
        "predicted": {
            "Затопление": int(predicted[0]),
            "Пожар": int(predicted[1]),
            "Утечка Газа": int(predicted[2]),
            "Проникновение": int(predicted[3]),
        },
        "confusion_matrix": confusion,
        "batch": batch,
    }


_prepare_qt_environment()

try:
    from PyQt5.QtWidgets import (
        QApplication,
        QCheckBox,
        QComboBox,
        QFileDialog,
        QGridLayout,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QTableWidget,
        QTableWidgetItem,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )
    from PyQt5.QtCore import QTimer

    PYQT_AVAILABLE = True
except ImportError as exc:
    QApplication = object  # type: ignore[assignment,misc]
    QMainWindow = object  # type: ignore[assignment,misc]
    QFileDialog = QMessageBox = QPushButton = QTextEdit = QWidget = object  # type: ignore[assignment,misc]
    QCheckBox = QComboBox = QLabel = QGridLayout = QVBoxLayout = QHBoxLayout = object  # type: ignore[assignment,misc]
    QTableWidget = QTableWidgetItem = QHeaderView = QTimer = object  # type: ignore[assignment,misc]
    PYQT_AVAILABLE = False
    PYQT_IMPORT_ERROR = exc


class SensorGeneratorWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.config = _load_config()
        self.setWindowTitle("Генератор сенсорных пакетов")
        self.resize(1120, 760)
        self._payload: Dict[str, object] = {}
        self._metrics_totals = self._empty_metrics()
        self._stream_timer = QTimer(self)
        self._stream_timer.setInterval(int(self.config["stream"]["interval_ms"]))
        self._stream_timer.timeout.connect(self._generate_once)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QWidget(self)
        self.setCentralWidget(root)
        main_layout = QVBoxLayout(root)

        controls = QGridLayout()
        controls.addWidget(QLabel("Источник:"), 0, 0)
        self.source_box = QComboBox()
        for option in SOURCE_OPTIONS:
            self.source_box.addItem(option["label"], option["key"])
        controls.addWidget(self.source_box, 0, 1)
        controls.addWidget(
            QLabel(f"Окрестность (из конфига): радиус = {self.config['neighborhood']['radius']}"),
            1,
            0,
            1,
            4,
        )

        self.fire_alarm_box = QCheckBox("Пожар")
        self.flood_alarm_box = QCheckBox("Затопление")
        self.gas_leak_alarm_box = QCheckBox("Утечка Газа")
        self.intrusion_alarm_box = QCheckBox("Проникновение")
        controls.addWidget(self.fire_alarm_box, 2, 0, 1, 1)
        controls.addWidget(self.flood_alarm_box, 2, 1, 1, 1)
        controls.addWidget(self.gas_leak_alarm_box, 2, 2, 1, 1)
        controls.addWidget(self.intrusion_alarm_box, 2, 3, 1, 1)

        main_layout.addLayout(controls)

        button_row = QHBoxLayout()
        self.btn_start = QPushButton("Старт")
        self.btn_start.clicked.connect(self._start_stream)
        button_row.addWidget(self.btn_start)

        self.btn_stop = QPushButton("Стоп")
        self.btn_stop.clicked.connect(self._stop_stream)
        self.btn_stop.setEnabled(False)
        button_row.addWidget(self.btn_stop)

        btn_reset = QPushButton("Обнулить")
        btn_reset.clicked.connect(self._reset_view)
        button_row.addWidget(btn_reset)

        btn_save = QPushButton("Сохранить JSON")
        btn_save.clicked.connect(self._save_json)
        button_row.addWidget(btn_save)
        main_layout.addLayout(button_row)

        self.note = QLabel(
            "Если галочки сняты: безопасная окрестность (без сработок). "
            "Галочки смещают окрестность в зону сработок. "
            "Для режимов «Безопасный датасет»/«Полный датасет» подтягиваются строки "
            "под выбранные сработки. "
            "Сид берется автоматически как текущее Unix-время в секундах."
        )
        self.note.setWordWrap(True)
        main_layout.addWidget(self.note)
        self.dataset_status = QLabel("Датасет: не использован.")
        main_layout.addWidget(self.dataset_status)

        self.metrics_table = QTableWidget(4, 4)
        self.metrics_table.setVerticalHeaderLabels(
            [
                "TP — Истинно-положительные",
                "FP — Ложно-положительные",
                "TN — Истинно-отрицательные",
                "FN — Ложно-отрицательные",
            ]
        )
        self.metrics_table.setHorizontalHeaderLabels(DETECTOR_LABELS)
        self.metrics_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        main_layout.addWidget(self.metrics_table)
        self._fill_metrics(self._metrics_totals)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        main_layout.addWidget(self.output)

    def _profile(self) -> Dict[str, bool]:
        return {
            "fire": self.fire_alarm_box.isChecked(),
            "flood": self.flood_alarm_box.isChecked(),
            "gas_leak": self.gas_leak_alarm_box.isChecked(),
            "intrusion": self.intrusion_alarm_box.isChecked(),
        }

    @staticmethod
    def _empty_metrics() -> Dict[str, Dict[str, int]]:
        return {detector: {"TP": 0, "FP": 0, "TN": 0, "FN": 0} for detector in DETECTOR_LABELS}

    def _source_label(self, source: str) -> str:
        for option in SOURCE_OPTIONS:
            if source == option["key"]:
                return option["label"]
        return source

    def _accumulate_metrics(self, confusion_matrix: Mapping[str, Mapping[str, int]]) -> None:
        for detector in DETECTOR_LABELS:
            detector_metrics = confusion_matrix.get(detector, {})
            totals = self._metrics_totals.setdefault(detector, {"TP": 0, "FP": 0, "TN": 0, "FN": 0})
            for metric in ("TP", "FP", "TN", "FN"):
                totals[metric] += int(detector_metrics.get(metric, 0))

    def _fill_metrics(self, confusion_matrix: Mapping[str, Mapping[str, int]]) -> None:
        for col, detector in enumerate(DETECTOR_LABELS):
            metrics = confusion_matrix.get(detector, {})
            for row, metric_name in enumerate(METRICS_ROW_ORDER):
                self.metrics_table.setItem(row, col, QTableWidgetItem(str(int(metrics.get(metric_name, 0)))))

    def _update_dataset_status(self) -> None:
        if not self._payload:
            self.dataset_status.setText("Датасет: не использован.")
            return
        source = str(self._payload.get("source", ""))
        source_label = self._source_label(source)
        if source == "synthetic":
            self.dataset_status.setText(f"Источник: {source_label} (без чтения CSV).")
            return
        idx = self._payload.get("selected_dataset_row_index")
        path = self._payload.get("dataset_path", "")
        self.dataset_status.setText(f"Источник: {source_label}, строка CSV: {idx}, файл: {path}")

    def _generate_once(self) -> bool:
        try:
            seed = int(time.time())
            source = str(self.source_box.currentData())
            profile = self._profile()
            self._payload = generate_profiled_batch(source=source, profile=profile, seed=seed, config=self.config)
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка генерации", str(exc))
            return False
        self._accumulate_metrics(self._payload.get("confusion_matrix", {}))
        self._fill_metrics(self._metrics_totals)
        self.output.setPlainText(json.dumps(self._payload, ensure_ascii=False, indent=2))
        self._update_dataset_status()
        return True

    def _start_stream(self) -> None:
        if not self._generate_once():
            return
        self._stream_timer.start()
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)

    def _stop_stream(self) -> None:
        self._stream_timer.stop()
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)

    def _reset_view(self) -> None:
        self._stop_stream()
        self._payload = {}
        self._metrics_totals = self._empty_metrics()
        self.output.clear()
        self._fill_metrics(self._metrics_totals)
        self._update_dataset_status()

    def _save_json(self) -> None:
        text = self.output.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Сохранение JSON", "Нет данных для сохранения.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить сгенерированный пакет",
            str(Path.cwd() / "generated_sensor_batch.json"),
            "Файлы JSON (*.json);;Все файлы (*)",
        )
        if not path:
            return
        Path(path).write_text(text, encoding="utf-8")


def main() -> None:
    if not PYQT_AVAILABLE:
        raise SystemExit("Для qt_sensor_generator.py требуется PyQt5.") from PYQT_IMPORT_ERROR
    app = QApplication(sys.argv)
    win = SensorGeneratorWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
