import io
import os
import sys
from typing import List, Optional, Tuple

import PyQt5
plugin_path = os.path.join(os.path.dirname(PyQt5.__file__), "Qt5", "plugins")
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plugin_path

import numpy as np
import scipy
import pandas as pd
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt, QTimer
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform, pdist
from sklearn.cluster import AgglomerativeClustering
from sklearn.datasets import make_blobs
from sklearn.metrics import silhouette_score
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler


STD_EPS = 1e-12
SCORE_EPS = 1e-6
MISSING_ATTEMPT_MULTIPLIER = 5
SPLINE_ORDER = 3
REL_ERROR_CLIP = 10.0
REL_ERROR_DENOM_FRAC = 0.01


def correlation_distance(a: np.ndarray, b: np.ndarray) -> float:
    """Возвращает расстояние на основе корреляции Пирсона (A4=3)."""
    if a.ndim > 1:
        a = a.ravel()
    if b.ndim > 1:
        b = b.ravel()
    if np.std(a) <= STD_EPS or np.std(b) <= STD_EPS:
        return float(np.linalg.norm(a - b))
    corr = np.corrcoef(a, b)[0, 1]
    if np.isnan(corr):
        return float(np.linalg.norm(a - b))
    return float(1 - corr)


def compactness_score(data: np.ndarray, labels: np.ndarray) -> float:
    """Метрика компактности кластеров (A6=5)."""
    total = 0.0
    count = 0
    for lbl in np.unique(labels):
        cluster_points = data[labels == lbl]
        if len(cluster_points) == 0:
            continue
        center = cluster_points.mean(axis=0)
        dists = np.linalg.norm(cluster_points - center, axis=1)
        total += dists.sum()
        count += len(dists)
    return total / count if count else 0.0


class AlgoWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Восстановление и кластеризация данных")
        self.resize(1100, 800)

        self.df_original: Optional[pd.DataFrame] = None
        self.df_with_gaps: Optional[pd.DataFrame] = None
        self.df_filled: Optional[pd.DataFrame] = None
        self.selected_features: List[str] = []
        self._last_distribution_image: Optional[bytes] = None

        central = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central)

        layout.addWidget(self._build_dataset_block())
        layout.addWidget(self._build_missing_block())
        layout.addWidget(self._build_recovery_block())
        layout.addWidget(self._build_cluster_block())
        layout.addWidget(self._build_distribution_block())
        layout.addWidget(self._build_evaluation_block())

        self.setCentralWidget(central)
        self._log("Загрузите CSV или сгенерируйте датасет для начала работы.")

    def _build_dataset_block(self) -> QtWidgets.QGroupBox:
        box = QtWidgets.QGroupBox("1. Подготовка датасета и базовая статистика")
        layout = QtWidgets.QGridLayout(box)

        load_btn = QtWidgets.QPushButton("Загрузить CSV")
        load_btn.clicked.connect(self.load_dataset)

        stats_btn = QtWidgets.QPushButton("Рассчитать базовую статистику (средн/мед/мода+распределение)")
        stats_btn.clicked.connect(self.show_stats)

        self.dataset_info = QtWidgets.QLabel("Датасет не загружен.")
        self.dataset_info.setWordWrap(True)

        layout.addWidget(load_btn, 0, 0)
        layout.addWidget(stats_btn, 0, 1)
        layout.addWidget(self.dataset_info, 1, 0, 1, 2)
        return box

    def _build_missing_block(self) -> QtWidgets.QGroupBox:
        box = QtWidgets.QGroupBox("2. Создание пропусков")
        layout = QtWidgets.QHBoxLayout(box)

        self.missing_combo = QtWidgets.QComboBox()
        self.missing_combo.addItems(["3%", "5%", "10%", "20%", "30%"])
        missing_btn = QtWidgets.QPushButton("Вставить пропуски")
        missing_btn.clicked.connect(self.apply_missing_blocks)

        save_spoiled_btn = QtWidgets.QPushButton("Скачать CSV с пропусками")
        save_spoiled_btn.clicked.connect(self.save_spoiled_dataset)

        load_spoiled_btn = QtWidgets.QPushButton("Загрузить CSV с пропусками")
        load_spoiled_btn.clicked.connect(self.load_spoiled_dataset)

        self.missing_info = QtWidgets.QLabel("Пропуски не созданы.")
        self.missing_info.setWordWrap(True)

        layout.addWidget(QtWidgets.QLabel("Доля пропусков:"))
        layout.addWidget(self.missing_combo)
        layout.addWidget(missing_btn)
        layout.addWidget(save_spoiled_btn)
        layout.addWidget(load_spoiled_btn)
        layout.addWidget(self.missing_info)
        return box

    def _build_recovery_block(self) -> QtWidgets.QGroupBox:
        box = QtWidgets.QGroupBox("3. Восстановление пропусков")
        layout = QtWidgets.QGridLayout(box)

        mode_btn = QtWidgets.QPushButton("Заполнение модой ")
        mode_btn.clicked.connect(self.fill_mode)

        spline_btn = QtWidgets.QPushButton("Сплайн-интерполяция")
        spline_btn.clicked.connect(self.fill_spline)

        stats_btn = QtWidgets.QPushButton("Статистика (ср./мед./мода)")
        stats_btn.clicked.connect(self.show_stats)

        save_stats_btn = QtWidgets.QPushButton("Скачать датасет со статистикой")
        save_stats_btn.clicked.connect(self.save_stats_dataset)

        load_stats_btn = QtWidgets.QPushButton("Загрузить датасет со статистикой")
        load_stats_btn.clicked.connect(self.load_stats_dataset)

        self.stats_view = QtWidgets.QTextEdit()
        self.stats_view.setReadOnly(True)

        layout.addWidget(mode_btn, 0, 0)
        layout.addWidget(spline_btn, 0, 1)
        layout.addWidget(stats_btn, 0, 2)
        layout.addWidget(save_stats_btn, 0, 3)
        layout.addWidget(load_stats_btn, 0, 4)
        layout.addWidget(self.stats_view, 1, 0, 1, 5)
        return box

    def _build_cluster_block(self) -> QtWidgets.QGroupBox:
        box = QtWidgets.QGroupBox("4. Кластеризация и классификация")
        layout = QtWidgets.QGridLayout(box)

        self.cluster_spin = QtWidgets.QSpinBox()
        self.cluster_spin.setRange(2, 12)
        self.cluster_spin.setValue(3)

        cluster_btn = QtWidgets.QPushButton("Кластеризовать по CURE")
        cluster_btn.clicked.connect(self.run_clustering)

        select_btn = QtWidgets.QPushButton("Выбор признаков по SFS")
        select_btn.clicked.connect(self.select_features)

        save_cluster_btn = QtWidgets.QPushButton("Скачать результат кластеризации")
        save_cluster_btn.clicked.connect(self.save_clustered_dataset)

        self.results_view = QtWidgets.QTextEdit()
        self.results_view.setReadOnly(True)

        layout.addWidget(QtWidgets.QLabel("Число кластеров:"), 0, 0)
        layout.addWidget(self.cluster_spin, 0, 1)
        layout.addWidget(cluster_btn, 0, 2)
        layout.addWidget(select_btn, 0, 3)
        layout.addWidget(save_cluster_btn, 0, 4)
        layout.addWidget(self.results_view, 1, 0, 1, 5)
        return box

    def _build_distribution_block(self) -> QtWidgets.QGroupBox:
        box = QtWidgets.QGroupBox("5. Распределение данных (перед/после восстановления)")
        layout = QtWidgets.QVBoxLayout(box)

        self.distribution_label = QtWidgets.QLabel("Гистограмма появится после расчётов.")
        self.distribution_label.setAlignment(Qt.AlignCenter)
        self.distribution_label.setMinimumHeight(240)
        self.hist_column_combo = QtWidgets.QComboBox()
        self.hist_column_combo.currentIndexChanged.connect(self._redraw_distribution_selected)

        save_img_btn = QtWidgets.QPushButton("Скачать гистограмму")
        save_img_btn.clicked.connect(self.save_distribution_image)

        layout.addWidget(self.distribution_label)
        layout.addWidget(QtWidgets.QLabel("Признак для гистограммы:"))
        layout.addWidget(self.hist_column_combo)
        layout.addWidget(save_img_btn)
        return box

    def _build_evaluation_block(self) -> QtWidgets.QGroupBox:
        box = QtWidgets.QGroupBox("6. Оценка результатов и сравнение методов")
        layout = QtWidgets.QVBoxLayout(box)

        compare_btn = QtWidgets.QPushButton("Сравнить оригинал / испорченный / восстановленный")
        compare_btn.clicked.connect(self.compare_results)

        eff_btn = QtWidgets.QPushButton("Сравнение эффективности методов восстановления")
        eff_btn.clicked.connect(self.run_efficiency_analysis)

        save_eval_btn = QtWidgets.QPushButton("Скачать отчёт оценки")
        save_eval_btn.clicked.connect(self.save_evaluation_report)

        self.evaluation_view = QtWidgets.QTextEdit()
        self.evaluation_view.setReadOnly(True)

        layout.addWidget(compare_btn)
        layout.addWidget(eff_btn)
        layout.addWidget(save_eval_btn)
        layout.addWidget(self.evaluation_view)
        return box

    def save_distribution_image(self) -> None:
        if self._last_distribution_image is None:
            QtWidgets.QMessageBox.warning(self, "Нет данных", "Сначала постройте распределение.")
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Сохранить гистограмму", "distribution.png", "PNG Files (*.png);;All Files (*)"
        )
        if not path:
            return
        try:
            with open(path, "wb") as f:
                f.write(self._last_distribution_image)
            self._log(f"Гистограмма сохранена: {os.path.basename(path)}")
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {exc}")

    def save_evaluation_report(self) -> None:
        text = self.evaluation_view.toPlainText()
        if not text.strip():
            QtWidgets.QMessageBox.warning(self, "Нет отчёта", "Сначала выполните оценку.")
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Сохранить отчёт оценки", "evaluation_report.txt", "Text Files (*.txt);;All Files (*)"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            self._log(f"Отчёт сохранён: {os.path.basename(path)}")
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {exc}")

    # --- Actions ---------------------------------------------------------
    def load_dataset(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Выберите CSV", "", "CSV Files (*.csv);;All Files (*)"
        )
        if not path:
            return
        try:
            try:
                df = pd.read_csv(path, sep=";", encoding="utf-8-sig")
            except Exception:
                df = pd.read_csv(path, encoding="utf-8-sig")
            self.df_original = df.reset_index(drop=True)
            self.df_with_gaps = self.df_original.copy()
            self.df_filled = None
            self.selected_features = []
            self.dataset_info.setText(
                f"Загружен файл: {os.path.basename(path)} ({len(df)} строк, {len(df.columns)} столбцов)"
            )
            self._log("Файл загружен. Сформируйте пропуски или сразу рассчитайте статистику.")
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить файл: {exc}")

    def apply_missing_blocks(self) -> None:
        if self.df_original is None:
            QtWidgets.QMessageBox.warning(self, "Нет данных", "Сначала загрузите датасет.")
            return
        percent = int(self.missing_combo.currentText().replace("%", ""))
        df = self.df_original.copy()
        total_cells = df.shape[0] * df.shape[1]
        target_missing = max(1, int(total_cells * percent / 100))
        block_shapes = [(2, 2), (3, 3), (4, 2)]
        rng = np.random.default_rng(42)

        missing = 0
        attempts = 0
        while missing < target_missing and attempts < target_missing * MISSING_ATTEMPT_MULTIPLIER:
            h, w = block_shapes[int(rng.integers(0, len(block_shapes)))]
            r = rng.integers(0, max(1, df.shape[0] - h + 1))
            c = rng.integers(0, max(1, df.shape[1] - w + 1))
            df.iloc[r : r + h, c : c + w] = np.nan
            missing = int(df.isna().sum().sum())
            attempts += 1

        self.df_with_gaps = df
        self.df_filled = None
        self.missing_info.setText(
            f"Пропуски: {missing} ячеек (~{missing / total_cells * 100:.2f}%)."
        )
        self._log("Пропуски созданы блоками 2x2, 3x3, 4x2.")

    def save_spoiled_dataset(self) -> None:
        if self.df_with_gaps is None:
            QtWidgets.QMessageBox.warning(self, "Нет данных", "Сначала испортите или загрузите испорченный датасет.")
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Сохранить испорченный CSV", "spoiled_dataset.csv", "CSV Files (*.csv);;All Files (*)"
        )
        if not path:
            return
        try:
            self.df_with_gaps.to_csv(path, sep=";", index=False, encoding="utf-8-sig")
            self._log(f"Испорченный датасет сохранён: {os.path.basename(path)}")
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {exc}")

    def load_spoiled_dataset(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Загрузить испорченный CSV", "", "CSV Files (*.csv);;All Files (*)"
        )
        if not path:
            return
        try:
            try:
                df = pd.read_csv(path, sep=";", encoding="utf-8-sig")
            except Exception:
                df = pd.read_csv(path, encoding="utf-8-sig")
            self.df_with_gaps = df.reset_index(drop=True)
            self.df_original = df.copy()
            self.df_filled = None
            self.missing_info.setText(f"Загружен испорченный датасет: {os.path.basename(path)} ({len(df)} строк)")
            self._log("Испортённый датасет загружен.")
            self.show_stats()
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить: {exc}")

    def fill_mode(self) -> None:
        if self.df_with_gaps is None:
            QtWidgets.QMessageBox.warning(self, "Нет данных", "Сначала создайте пропуски.")
            return
        df = self.df_with_gaps.copy()
        for col in df.columns:
            if not df[col].isna().any():
                continue
            if pd.api.types.is_numeric_dtype(df[col]):
                mode_values = df[col].mode(dropna=True)
                fill_value = mode_values.iloc[0] if not mode_values.empty else df[col].mean()
                df[col] = df[col].fillna(fill_value)
            else:
                mode_values = df[col].mode(dropna=True)
                fill_value = mode_values.iloc[0] if not mode_values.empty else ""
                df[col] = df[col].fillna(fill_value)
        self.df_filled = df
        self._log("Пропуски заполнены модой.")
        self.show_stats()

    def fill_spline(self) -> None:
        if self.df_with_gaps is None:
            QtWidgets.QMessageBox.warning(self, "Нет данных", "Сначала создайте пропуски.")
            return
        df = self.df_with_gaps.copy()
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        for col in numeric_cols:
            try:
                df[col] = df[col].interpolate(method="spline", order=SPLINE_ORDER, limit_direction="both")
            except (ValueError, TypeError):
                df[col] = df[col].interpolate(method="linear", limit_direction="both")
            except Exception:
                df[col] = df[col].interpolate(method="linear", limit_direction="both")
            mode_values = df[col].mode(dropna=True)
            if df[col].isna().any():
                df[col] = df[col].fillna(mode_values.iloc[0] if not mode_values.empty else 0)

        for col in df.columns:
            if col in numeric_cols:
                continue
            mode_values = df[col].mode(dropna=True)
            fill_value = mode_values.iloc[0] if not mode_values.empty else ""
            df[col] = df[col].fillna(fill_value)

        self.df_filled = df
        self._log("Пропуски восстановлены сплайн-интерполяцией (A1=11).")
        self.show_stats()

    def save_stats_dataset(self) -> None:
        target_df = self._choose_df()
        if target_df is None:
            QtWidgets.QMessageBox.warning(self, "Нет данных", "Сначала загрузите или создайте датасет.")
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Сохранить датасет со статистикой", "stats_dataset.csv", "CSV Files (*.csv);;All Files (*)"
        )
        if not path:
            return
        try:
            target_df.to_csv(path, sep=";", index=False, encoding="utf-8-sig")
            stats_path = os.path.splitext(path)[0] + "_report.txt"
            with open(stats_path, "w", encoding="utf-8") as f:
                parts = [
                    self._stats_text(self.df_original, "Исходные данные") if self.df_original is not None else "",
                    self._stats_text(self.df_with_gaps, "С пропусками") if self.df_with_gaps is not None else "",
                    self._stats_text(self.df_filled, "После восстановления") if self.df_filled is not None else "",
                ]
                f.write("\n\n".join([p for p in parts if p]))
            self._log(f"Датасет и отчет сохранены: {os.path.basename(path)}")
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {exc}")

    def load_stats_dataset(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Загрузить датасет со статистикой", "", "CSV Files (*.csv);;All Files (*)"
        )
        if not path:
            return
        try:
            try:
                df = pd.read_csv(path, sep=";", encoding="utf-8-sig")
            except Exception:
                df = pd.read_csv(path, encoding="utf-8-sig")
            self.df_original = df.reset_index(drop=True)
            self.df_with_gaps = self.df_original.copy()
            self.df_filled = None
            self.dataset_info.setText(f"Загружен датасет со статистикой: {os.path.basename(path)} ({len(df)} строк)")
            self._log("Датасет со статистикой загружен.")
            self.show_stats()
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить: {exc}")

    def _stats_text(self, df: pd.DataFrame, title: str) -> str:
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        if not numeric_cols:
            return f"{title}: нет числовых столбцов."
        lines = [title]
        for col in numeric_cols:
            col_mean = df[col].mean()
            col_median = df[col].median()
            mode_series = df[col].mode(dropna=True)
            col_mode = mode_series.iloc[0] if not mode_series.empty else "—"
            lines.append(
                f"{col}: ср={col_mean:.4f}, мед={col_median:.4f}, мода={col_mode}"
            )
        return "\n".join(lines)

    def show_stats(self) -> None:
        if self.df_original is None:
            QtWidgets.QMessageBox.warning(self, "Нет данных", "Сначала загрузите датасет.")
            return
        target_df = self._choose_df()
        text = []
        if self.df_original is not None:
            text.append(self._stats_text(self.df_original, "Исходные данные"))
        if self.df_with_gaps is not None:
            text.append(self._stats_text(self.df_with_gaps, "С пропусками"))
        if self.df_filled is not None:
            text.append(self._stats_text(self.df_filled, "После восстановления"))
        self.stats_view.setPlainText("\n\n".join(text))
        self._prepare_hist_columns(target_df)
        self._draw_distribution(target_df)

    def select_features(self) -> None:
        if self.df_filled is None:
            QtWidgets.QMessageBox.warning(self, "Нет данных", "Сначала восстановите пропуски.")
            return
        df = self.df_filled
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        numeric_cols = [c for c in numeric_cols if c.lower() != "класс"]
        if not numeric_cols:
            QtWidgets.QMessageBox.warning(self, "Нет признаков", "Не найдены числовые признаки.")
            return

        n_clusters = self.cluster_spin.value()
        sample_df = df[numeric_cols]
        if len(sample_df) > 2000:
            sample_df = sample_df.sample(2000, random_state=42)

        remaining = numeric_cols.copy()
        selected: List[str] = []
        best_score = -np.inf

        def silhouette_for_features(cols: List[str]) -> float:
            if len(cols) == 0:
                return -np.inf
            data = sample_df[cols].dropna()
            if len(data) < n_clusters + 1:
                return -np.inf
            scaler = StandardScaler()
            scaled = scaler.fit_transform(data)
            dist = 1 - np.corrcoef(scaled)
            dist = np.nan_to_num(dist, nan=0.0)
            clustering = AgglomerativeClustering(
                n_clusters=n_clusters, metric="precomputed", linkage="average"
            )
            labels = clustering.fit_predict(dist)
            try:
                return silhouette_score(dist, labels, metric="precomputed")
            except Exception:
                return -np.inf

        while remaining:
            trial_scores: List[Tuple[float, str]] = []
            for col in remaining:
                score = silhouette_for_features(selected + [col])
                trial_scores.append((score, col))
            score, col = max(trial_scores, key=lambda x: x[0])
            if score > best_score + SCORE_EPS:
                best_score = score
                selected.append(col)
                remaining.remove(col)
            else:
                break

        self.selected_features = selected if selected else numeric_cols
        self._log(f"Выбранные признаки (A3=4): {', '.join(self.selected_features)}.")
        self.results_view.append(f"Признаки для кластеризации: {', '.join(self.selected_features)}")

    def run_clustering(self) -> None:
        if self.df_filled is None:
            QtWidgets.QMessageBox.warning(self, "Нет данных", "Сначала восстановите пропуски.")
            return
        df = self.df_filled.copy()
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        if not numeric_cols:
            QtWidgets.QMessageBox.warning(self, "Нет признаков", "Не найдены числовые признаки.")
            return

        features = self.selected_features or numeric_cols
        data = df[features].copy().replace([np.inf, -np.inf], np.nan).dropna()
        if data.empty:
            QtWidgets.QMessageBox.warning(self, "Нет данных", "После очистки данные пусты.")
            return

        n_clusters = self.cluster_spin.value()
        if len(data) > 2000:
            sample_data = data.sample(2000, random_state=42)
        else:
            sample_data = data

        if len(sample_data) < 2:
            QtWidgets.QMessageBox.warning(self, "Недостаточно данных", "Нужно минимум 2 строки для кластеризации.")
            return
        if np.all(np.std(sample_data.values, axis=0) <= STD_EPS):
            QtWidgets.QMessageBox.warning(self, "Недостаточно разброса", "Все признаки имеют нулевую дисперсию.")
            return

        stds = sample_data.std(axis=0)
        if np.any(stds <= STD_EPS):
            condensed = pdist(sample_data.values, metric="euclidean")
        else:
            corr_matrix = np.corrcoef(sample_data.values)
            corr_matrix = np.nan_to_num(corr_matrix, nan=0.0, posinf=0.0, neginf=0.0)
            distance_matrix = 1 - corr_matrix
            np.fill_diagonal(distance_matrix, 0.0)
            condensed = squareform(distance_matrix, checks=False)

        Z = linkage(condensed, method="median")
        labels_sample = fcluster(Z, t=n_clusters, criterion="maxclust")

        representatives = self._cure_representatives(
            sample_data.values, labels_sample, shrink=0.5, per_cluster=5
        )

        default_label = representatives[0][0] if representatives else 1
        assigned_labels = []
        for row in data.values:
            best_lbl = None
            best_dist = float("inf")
            for lbl, reps in representatives:
                rep_dists = [correlation_distance(row, rp) for rp in reps]
                d = float(np.min(rep_dists)) if rep_dists else float("inf")
                if d < best_dist:
                    best_dist = d
                    best_lbl = lbl
            assigned_labels.append(int(best_lbl) if best_lbl is not None else int(default_label))
        assigned_labels = np.array(assigned_labels, dtype=int)

        compactness = compactness_score(data.values, assigned_labels)
        df.loc[data.index, "cluster"] = assigned_labels

        classification_info = self._run_classification(df, features)

        result_lines = [
            f"Метод: CURE и linkage=median, расстояние=корреляция, кластеров={n_clusters}",
            f"Компактность кластеров: {compactness:.4f}",
        ]
        if classification_info:
            result_lines.append(classification_info)

        self.df_filled = df
        self.results_view.setPlainText("\n".join(result_lines))
        self._log("Кластеризация выполнена.")

    def save_clustered_dataset(self) -> None:
        if self.df_filled is None or "cluster" not in self.df_filled.columns:
            QtWidgets.QMessageBox.warning(self, "Нет кластеров", "Сначала выполните кластеризацию.")
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Сохранить кластеризованный CSV", "clustered_dataset.csv", "CSV Files (*.csv);;All Files (*)"
        )
        if not path:
            return
        try:
            self.df_filled.to_csv(path, sep=";", index=False, encoding="utf-8-sig")
            self._log(f"Кластеризованный датасет сохранён: {os.path.basename(path)}")
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {exc}")

    def _run_classification(self, df: pd.DataFrame, features: List[str]) -> Optional[str]:
        if "Класс" not in df.columns:
            return None
        usable = df.dropna(subset=features + ["Класс"])
        if usable.empty:
            return None
        X = usable[features]
        y = usable["Класс"].astype(int)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42, stratify=y
        )
        clf = KNeighborsClassifier(n_neighbors=5)
        try:
            clf.fit(X_train, y_train)
            acc = clf.score(X_test, y_test)
        except ValueError:
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42
            )
            clf.fit(X_train, y_train)
            acc = clf.score(X_test, y_test)
        return f"Классификация (kNN) по восстановленным данным: точность {acc:.3f}"

    # --- Helpers ---------------------------------------------------------
    def _cure_representatives(
        self, data: np.ndarray, labels: np.ndarray, shrink: float = 0.5, per_cluster: int = 5
    ) -> List[Tuple[int, np.ndarray]]:
        reps: List[Tuple[int, np.ndarray]] = []
        for lbl in np.unique(labels):
            pts = data[labels == lbl]
            if len(pts) == 0:
                continue
            centroid = pts.mean(axis=0)
            dists = np.linalg.norm(pts - centroid, axis=1)
            order = np.argsort(dists)[::-1]
            chosen = pts[order[:per_cluster]]
            shrunk = centroid + shrink * (chosen - centroid)
            reps.append((int(lbl), shrunk))
        return reps

    def _choose_df(self) -> Optional[pd.DataFrame]:
        if self.df_filled is not None:
            return self.df_filled
        if self.df_with_gaps is not None:
            return self.df_with_gaps
        return self.df_original

    def _stats_summary(self, df: pd.DataFrame, title: str) -> str:
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        lines = [title]
        for col in numeric_cols:
            mode_series = df[col].mode(dropna=True)
            col_mode = mode_series.iloc[0] if not mode_series.empty else "—"
            lines.append(
                f"{col}: mean={df[col].mean():.4f}, median={df[col].median():.4f}, mode={col_mode}"
            )
        return "\n".join(lines) if numeric_cols else f"{title}: нет числовых столбцов."

    def compare_results(self) -> None:
        if self.df_original is None:
            QtWidgets.QMessageBox.warning(self, "Нет данных", "Сначала загрузите датасет.")
            return
        parts = []
        parts.append(self._stats_summary(self.df_original, "Оригинал"))
        if self.df_with_gaps is not None:
            parts.append(self._stats_summary(self.df_with_gaps, "Испортённый"))
        if self.df_filled is not None:
            parts.append(self._stats_summary(self.df_filled, "Восстановленный"))
        self.evaluation_view.setPlainText("\n\n".join(parts))

    def _block_missing(self, df: pd.DataFrame, percent: float, seed: int = 42) -> pd.DataFrame:
        rng = np.random.default_rng(seed)
        df_copy = df.copy()
        total_cells = df_copy.shape[0] * df_copy.shape[1]
        target_missing = max(1, int(total_cells * percent))
        block_shapes = [(2, 2), (3, 3), (4, 2)]
        missing = 0
        attempts = 0
        while missing < target_missing and attempts < target_missing * MISSING_ATTEMPT_MULTIPLIER:
            h, w = block_shapes[int(rng.integers(0, len(block_shapes)))]
            r = rng.integers(0, max(1, df_copy.shape[0] - h + 1))
            c = rng.integers(0, max(1, df_copy.shape[1] - w + 1))
            df_copy.iloc[r : r + h, c : c + w] = np.nan
            missing = int(df_copy.isna().sum().sum())
            attempts += 1
        return df_copy

    def _fill_mode_df(self, df: pd.DataFrame) -> pd.DataFrame:
        filled = df.copy()
        for col in filled.columns:
            if not filled[col].isna().any():
                continue
            if pd.api.types.is_numeric_dtype(filled[col]):
                mode_values = filled[col].mode(dropna=True)
                fill_value = mode_values.iloc[0] if not mode_values.empty else filled[col].mean()
                filled[col] = filled[col].fillna(fill_value)
            else:
                mode_values = filled[col].mode(dropna=True)
                fill_value = mode_values.iloc[0] if not mode_values.empty else ""
                filled[col] = filled[col].fillna(fill_value)
        return filled

    def _fill_spline_df(self, df: pd.DataFrame) -> pd.DataFrame:
        filled = df.copy()
        numeric_cols = [c for c in filled.columns if pd.api.types.is_numeric_dtype(filled[c])]
        for col in numeric_cols:
            try:
                filled[col] = filled[col].interpolate(method="spline", order=SPLINE_ORDER, limit_direction="both")
            except (ValueError, TypeError):
                filled[col] = filled[col].interpolate(method="linear", limit_direction="both")
            except Exception:
                filled[col] = filled[col].interpolate(method="linear", limit_direction="both")
            mode_values = filled[col].mode(dropna=True)
            if filled[col].isna().any():
                filled[col] = filled[col].fillna(mode_values.iloc[0] if not mode_values.empty else 0)
        for col in filled.columns:
            if col in numeric_cols:
                continue
            mode_values = filled[col].mode(dropna=True)
            fill_value = mode_values.iloc[0] if not mode_values.empty else ""
            filled[col] = filled[col].fillna(fill_value)
        return filled

    def _mae_stats(self, base: pd.DataFrame, other: pd.DataFrame) -> float:
        numeric_cols = [c for c in base.columns if pd.api.types.is_numeric_dtype(base[c])]
        if not numeric_cols:
            return float("nan")
        diffs = []
        for col in numeric_cols:
            diffs.append(abs(base[col].mean() - other[col].mean()))
            diffs.append(abs(base[col].median() - other[col].median()))
        return float(np.nanmean(diffs)) if diffs else float("nan")

    def run_efficiency_analysis(self) -> None:
        if self.df_original is None:
            QtWidgets.QMessageBox.warning(self, "Нет данных", "Сначала загрузите датасет.")
            return
        base_df = self.df_original.dropna().copy()
        if base_df.empty:
            QtWidgets.QMessageBox.warning(self, "Нет данных", "Нужен полный датасет без пропусков.")
            return
        numeric_cols = [c for c in base_df.columns if pd.api.types.is_numeric_dtype(base_df[c])]
        if not numeric_cols:
            QtWidgets.QMessageBox.warning(self, "Нет числовых данных", "Нет числовых столбцов для анализа.")
            return
        if len(base_df) > 5000:
            base_df = base_df.sample(5000, random_state=42)

        numeric_col_scales = {}
        for col in numeric_cols:
            if not base_df[col].notna().any():
                numeric_col_scales[col] = 1.0
                continue
            scale = float(np.nanmean(np.abs(base_df[col])))
            if not np.isfinite(scale) or scale <= STD_EPS:
                alt_scale = float(np.nanstd(base_df[col]))
                scale = alt_scale if np.isfinite(alt_scale) and alt_scale > STD_EPS else 1.0
            numeric_col_scales[col] = scale
        percents = [0.03, 0.05, 0.1, 0.2, 0.3]
        methods = {"mode": self._fill_mode_df, "spline": self._fill_spline_df}
        lines = ["Сравнение эффективности методов заполнения (суммарная относительная погрешность):"]
        for p in percents:
            spoiled = self._block_missing(base_df, p, seed=int(p * 1000))
            missing_mask = spoiled.isna()
            for name, func in methods.items():
                filled = func(spoiled)
                rel_errors = []
                clipped_ratios = []
                for col in numeric_cols:
                    col_mask = missing_mask[col]
                    if not col_mask.any():
                        continue
                    true_vals = base_df.loc[col_mask, col]
                    pred_vals = filled.loc[col_mask, col]
                    col_scale = numeric_col_scales.get(col, 1.0)
                    col_scale_safe = max(col_scale, 1.0)
                    denom_threshold = max(STD_EPS, REL_ERROR_DENOM_FRAC * col_scale_safe)
                    safe_denom = np.where(
                        np.abs(true_vals) <= denom_threshold,
                        col_scale_safe,
                        np.abs(true_vals),
                    )
                    rel_raw = np.abs(true_vals - pred_vals) / safe_denom
                    clipped_ratios.append(float(np.mean(rel_raw > REL_ERROR_CLIP)))
                    rel = np.clip(rel_raw, 0, REL_ERROR_CLIP)
                    rel_errors.append(np.mean(rel))
                score = float(np.nanmean(rel_errors)) if rel_errors else float("nan")
                clip_share = float(np.nanmean(clipped_ratios)) if clipped_ratios else 0.0
                lines.append(
                    f"Пропуски {int(p*100)}% | метод {name}: относительная ошибка={score:.4f}, "
                    f"клиппинг>{REL_ERROR_CLIP:.0f}: {clip_share*100:.1f}%"
                )
        self.evaluation_view.setPlainText("\n".join(lines))

    def _draw_distribution(self, df: pd.DataFrame) -> None:
        if df is None:
            self.distribution_label.setText("Нет данных для гистограммы.")
            return
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        if not numeric_cols:
            self.distribution_label.setText("Нет числовых столбцов для гистограммы.")
            return
        column = self.hist_column_combo.currentText() if self.hist_column_combo.count() > 0 else numeric_cols[0]
        if column not in numeric_cols:
            column = numeric_cols[0]
        fig = Figure(figsize=(6, 3))
        ax = fig.add_subplot(111)
        ax.hist(df[column].dropna(), bins=30, alpha=0.8, label=column)
        ax.legend()
        ax.set_title(f"Распределение: {column}")
        ax.grid(True, alpha=0.3)

        canvas = FigureCanvasAgg(fig)
        buffer = io.BytesIO()
        canvas.print_png(buffer)
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(buffer.getvalue(), "PNG")
        self.distribution_label.setPixmap(
            pixmap.scaled(600, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
        self._last_distribution_image = buffer.getvalue()

    def _prepare_hist_columns(self, df: Optional[pd.DataFrame]) -> None:
        self.hist_column_combo.clear()
        if df is None:
            return
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        self.hist_column_combo.addItems(numeric_cols[:10])

    def _redraw_distribution_selected(self) -> None:
        df = self._choose_df()
        self._draw_distribution(df)

    def _log(self, message: str) -> None:
        self.statusBar().showMessage(message, 5000)


def main() -> None:
    if "--screenshot" in sys.argv:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    app = QtWidgets.QApplication(sys.argv)
    window = AlgoWindow()
    window.show()

    if "--screenshot" in sys.argv:
        idx = sys.argv.index("--screenshot")
        path = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else "algo_app.png"
        def capture_and_quit() -> None:
            window.grab().save(path)
            QtWidgets.QApplication.instance().quit()

        QTimer.singleShot(800, capture_and_quit)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
