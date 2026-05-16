import os
import sys
from concurrent.futures import ProcessPoolExecutor
from typing import List, Optional, Sequence, Tuple

import PyQt5
from PyQt5 import QtCore, QtGui, QtWidgets

from algorithms import (
    AntColonySolver,
    GraphData,
    INF,
    SimulatedAnnealingSolver,
    build_control_graph,
    exact_hamiltonian_cycle_for_small_graph,
    format_route,
    parse_stp_graph,
)


plugin_path = os.path.join(os.path.dirname(PyQt5.__file__), "Qt5", "plugins")
if os.path.isdir(plugin_path):
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plugin_path

CANVAS_MARGIN_X = 10
CANVAS_MARGIN_TOP = 20
CANVAS_MARGIN_BOTTOM = 10
MAX_DRAWN_EDGES = 4000
MIN_ANT_ITERATIONS = 10
ANT_ITERATION_DIVISOR = 20
MAX_ANTS = 30
MIN_ANTS = 6
PARALLEL_WORKERS = 4
EVAPORATION_INPUT_SCALE_FACTOR = 10.0


def _solve_sa_worker(
    graph: GraphData,
    iterations: int,
    use_mods: bool,
    start_temp: Optional[float],
    cooling_rate: float,
    boltzmann_log_shift: float,
):
    solver = SimulatedAnnealingSolver(seed=42)
    return solver.solve(
        graph,
        iterations=iterations,
        use_boltzmann_mod=use_mods,
        start_temp=start_temp,
        cooling_rate=cooling_rate,
        boltzmann_log_shift=boltzmann_log_shift,
    )


def _solve_aco_worker(
    graph: GraphData,
    iterations: int,
    ant_count: int,
    alpha: float,
    beta: float,
    q: float,
    evaporation: float,
    use_mods: bool,
    elite_weight: float,
):
    solver = AntColonySolver(seed=42)
    return solver.solve(
        graph,
        iterations=iterations,
        ant_count=ant_count,
        alpha=alpha,
        beta=beta,
        q=q,
        evaporation=evaporation,
        use_elite_ants_mod=use_mods,
        elite_weight=elite_weight,
    )


class GraphCanvas(QtWidgets.QWidget):
    vertex_added = QtCore.pyqtSignal(float, float)

    def __init__(self, title: str, clickable: bool = False, show_base_edges: bool = True) -> None:
        super().__init__()
        self.title = title
        self.clickable = clickable
        self.show_base_edges = show_base_edges
        self.positions = {}
        self.edge_pairs: List[Tuple[int, int]] = []
        self.route: List[int] = []
        self.setMinimumSize(460, 350)
        self.setAutoFillBackground(True)

    def set_graph_positions(self, positions, distances=None) -> None:
        self.positions = dict(positions)
        self.edge_pairs = []
        if self.show_base_edges and distances is not None and self.positions:
            all_edges: List[Tuple[float, int, int]] = []
            n = min(len(distances), len(self.positions))
            for i in range(n):
                for j in range(i + 1, n):
                    d = min(distances[i][j], distances[j][i])
                    if d < INF:
                        all_edges.append((float(d), i, j))
            all_edges.sort(key=lambda item: item[0])
            self.edge_pairs = [(i, j) for _, i, j in all_edges[:MAX_DRAWN_EDGES]]
        self.update()

    def set_route(self, route: Optional[Sequence[int]]) -> None:
        self.route = list(route or [])
        self.update()

    def clear(self) -> None:
        self.positions = {}
        self.route = []
        self.update()

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if self.clickable and event.button() == QtCore.Qt.LeftButton:
            if hasattr(event, "position"):
                pos = event.position()
            elif hasattr(event, "localPos"):
                pos = event.localPos()
            else:
                pos = event.pos()
            x = float(pos.x())
            y = float(pos.y())
            if (
                CANVAS_MARGIN_X <= x <= self.width() - CANVAS_MARGIN_X
                and CANVAS_MARGIN_TOP <= y <= self.height() - CANVAS_MARGIN_BOTTOM
            ):
                self.vertex_added.emit(x, y)
        super().mousePressEvent(event)

    def _normalize_positions(self):
        if not self.positions:
            return {}
        xs = [float(v[0]) for v in self.positions.values()]
        ys = [float(v[1]) for v in self.positions.values()]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        x_range = max(1e-9, max_x - min_x)
        y_range = max(1e-9, max_y - min_y)
        draw_w = max(1.0, float(self.width() - 2 * CANVAS_MARGIN_X))
        draw_h = max(1.0, float(self.height() - CANVAS_MARGIN_TOP - CANVAS_MARGIN_BOTTOM))
        normalized = {}
        for idx, (x, y) in self.positions.items():
            nx = CANVAS_MARGIN_X + (float(x) - min_x) * draw_w / x_range
            ny = CANVAS_MARGIN_TOP + (float(y) - min_y) * draw_h / y_range
            normalized[idx] = (nx, ny)
        return normalized

    def paintEvent(self, _: QtGui.QPaintEvent) -> None:
        p = QtGui.QPainter(self)
        p.fillRect(self.rect(), QtGui.QColor("white"))

        p.setPen(QtGui.QPen(QtGui.QColor(140, 140, 140)))
        p.drawRect(1, 1, self.width() - 2, self.height() - 2)
        p.setPen(QtGui.QPen(QtGui.QColor(30, 30, 30)))
        p.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        p.drawText(8, 16, self.title)

        if not self.positions:
            p.setPen(QtGui.QPen(QtGui.QColor(120, 120, 120)))
            hint = "Кликните мышью для добавления вершин" if self.clickable else "Результат будет отображен здесь"
            p.drawText(16, self.height() // 2, hint)
            return

        norm_positions = self._normalize_positions()
        if self.show_base_edges:
            base_edge_pen = QtGui.QPen(QtGui.QColor(190, 190, 190))
            base_edge_pen.setWidth(1)
            p.setPen(base_edge_pen)
            for i, j in self.edge_pairs:
                a = norm_positions.get(i)
                b = norm_positions.get(j)
                if a is None or b is None:
                    continue
                p.drawLine(int(a[0]), int(a[1]), int(b[0]), int(b[1]))

        if len(self.route) >= 2:
            edge_pen = QtGui.QPen(QtGui.QColor(20, 140, 70))
            edge_pen.setWidth(2)
            p.setPen(edge_pen)
            for i in range(len(self.route) - 1):
                a = norm_positions.get(self.route[i])
                b = norm_positions.get(self.route[i + 1])
                if a is None or b is None:
                    continue
                p.drawLine(int(a[0]), int(a[1]), int(b[0]), int(b[1]))

        for idx, (x, y) in norm_positions.items():
            p.setBrush(QtGui.QColor(45, 110, 220))
            p.setPen(QtGui.QPen(QtGui.QColor(20, 20, 20)))
            p.drawEllipse(QtCore.QPointF(x, y), 7, 7)
            p.drawText(int(x + 8), int(y - 8), str(idx + 1))


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Algo2 / Second: TSP отжиг и муравьи")
        self.resize(1700, 860)

        self.graph = build_control_graph()
        self._cache = {}
        self._table_updates_blocked = False
        self.sa = SimulatedAnnealingSolver(seed=42)
        self.aco = AntColonySolver(seed=42)

        central = QtWidgets.QWidget()
        root = QtWidgets.QHBoxLayout(central)

        root.addWidget(self._build_left_panel(), 1)
        root.addWidget(self._build_middle_panel(), 2)
        root.addWidget(self._build_right_panel(), 2)

        self.setCentralWidget(central)

        self._refresh_all_views()
        self.statusBar().showMessage("Готово")

    def _build_left_panel(self) -> QtWidgets.QWidget:
        box = QtWidgets.QGroupBox("Алгоритмы и результаты")
        layout = QtWidgets.QVBoxLayout(box)

        self.algo_tabs = QtWidgets.QTabWidget()
        self.algo_tabs.addTab(self._build_sa_tab(), "Отжиг")
        self.algo_tabs.addTab(self._build_aco_tab(), "Муравьиный")
        layout.addWidget(self.algo_tabs)

        self.parallel_checkbox = QtWidgets.QCheckBox("Параллельный расчёт (до 4 процессов)")
        self.parallel_checkbox.setChecked(True)
        layout.addWidget(self.parallel_checkbox)
        return box

    def _build_sa_tab(self) -> QtWidgets.QWidget:
        panel = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(panel)
        form = QtWidgets.QFormLayout()

        self.sa_iter_input = QtWidgets.QSpinBox()
        self.sa_iter_input.setRange(10, 20000)
        self.sa_iter_input.setValue(500)
        form.addRow("Итерации", self.sa_iter_input)

        self.sa_start_temp_input = QtWidgets.QDoubleSpinBox()
        self.sa_start_temp_input.setRange(0.0, 1_000_000.0)
        self.sa_start_temp_input.setDecimals(3)
        self.sa_start_temp_input.setSingleStep(1.0)
        self.sa_start_temp_input.setValue(0.0)
        form.addRow("Начальная температура (0 = авто)", self.sa_start_temp_input)

        self.sa_cooling_rate_input = QtWidgets.QDoubleSpinBox()
        self.sa_cooling_rate_input.setRange(0.8, 0.999999)
        self.sa_cooling_rate_input.setDecimals(6)
        self.sa_cooling_rate_input.setSingleStep(0.001)
        self.sa_cooling_rate_input.setValue(0.997)
        form.addRow("Коэффициент охлаждения", self.sa_cooling_rate_input)

        self.sa_mod_checkbox = QtWidgets.QCheckBox("Включить модификацию: Больцмановский отжиг")
        self.sa_mod_checkbox.setChecked(True)
        form.addRow("Модификация", self.sa_mod_checkbox)

        self.sa_boltzmann_shift_input = QtWidgets.QDoubleSpinBox()
        self.sa_boltzmann_shift_input.setRange(0.001, 1000.0)
        self.sa_boltzmann_shift_input.setDecimals(3)
        self.sa_boltzmann_shift_input.setSingleStep(0.1)
        self.sa_boltzmann_shift_input.setValue(2.0)
        form.addRow("Параметр модификации (сдвиг Больцмана)", self.sa_boltzmann_shift_input)

        self.sa_mod_checkbox.toggled.connect(self._toggle_sa_mod_settings)
        self._toggle_sa_mod_settings(self.sa_mod_checkbox.isChecked())

        self.sa_calc_button = QtWidgets.QPushButton("Рассчитать (с графикой)")
        self.sa_calc_button.clicked.connect(self.calculate_sa)
        self.sa_calc_numbers_button = QtWidgets.QPushButton("Рассчитать без графики")
        self.sa_calc_numbers_button.clicked.connect(self.calculate_sa_without_graphics)

        self.sa_path_output = QtWidgets.QPlainTextEdit()
        self.sa_path_output.setReadOnly(True)
        self.sa_path_output.setPlaceholderText("Полученный кратчайший путь (SA)")
        self.sa_path_output.setMaximumHeight(110)

        self.sa_length_label = QtWidgets.QLabel("Длина кратчайшего пути: -")
        self.sa_report_output = QtWidgets.QPlainTextEdit()
        self.sa_report_output.setReadOnly(True)
        self.sa_report_output.setPlaceholderText("Результаты расчёта SA")

        layout.addLayout(form)
        layout.addWidget(self.sa_calc_button)
        layout.addWidget(self.sa_calc_numbers_button)
        layout.addWidget(QtWidgets.QLabel("Кратчайший путь (номера вершин):"))
        layout.addWidget(self.sa_path_output)
        layout.addWidget(self.sa_length_label)
        layout.addWidget(QtWidgets.QLabel("Отчёт SA:"))
        layout.addWidget(self.sa_report_output, 1)
        return panel

    def _build_aco_tab(self) -> QtWidgets.QWidget:
        panel = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(panel)
        form = QtWidgets.QFormLayout()

        self.alpha_input = QtWidgets.QDoubleSpinBox()
        self.alpha_input.setRange(0.0, 10.0)
        self.alpha_input.setValue(1.0)
        self.alpha_input.setSingleStep(0.1)

        self.beta_input = QtWidgets.QDoubleSpinBox()
        self.beta_input.setRange(0.0, 10.0)
        self.beta_input.setValue(3.0)
        self.beta_input.setSingleStep(0.1)

        self.q_input = QtWidgets.QDoubleSpinBox()
        self.q_input.setRange(0.001, 1000000.0)
        self.q_input.setValue(100.0)

        self.evap_input = QtWidgets.QDoubleSpinBox()
        self.evap_input.setRange(0.0, EVAPORATION_INPUT_SCALE_FACTOR)
        self.evap_input.setDecimals(2)
        self.evap_input.setSingleStep(0.1)
        self.evap_input.setValue(3.5)

        self.aco_iter_input = QtWidgets.QSpinBox()
        self.aco_iter_input.setRange(1, 5000)
        self.aco_iter_input.setValue(25)

        self.ant_count_input = QtWidgets.QSpinBox()
        self.ant_count_input.setRange(1, 1000)
        self.ant_count_input.setValue(30)

        self.aco_mod_checkbox = QtWidgets.QCheckBox("Включить модификацию: «Элитные» муравьи")
        self.aco_mod_checkbox.setChecked(True)

        self.aco_elite_weight_input = QtWidgets.QDoubleSpinBox()
        self.aco_elite_weight_input.setRange(0.1, 1000.0)
        self.aco_elite_weight_input.setDecimals(2)
        self.aco_elite_weight_input.setSingleStep(0.1)
        self.aco_elite_weight_input.setValue(5.0)

        form.addRow("Коэффициент значимости феромона α", self.alpha_input)
        form.addRow("Коэффициент значимости длины β", self.beta_input)
        form.addRow("Кол-во добавляемого феромона Q", self.q_input)
        form.addRow("Интенсивность испарения ρ", self.evap_input)
        form.addRow("Итерации", self.aco_iter_input)
        form.addRow("Кол-во муравьёв", self.ant_count_input)
        form.addRow("Модификация", self.aco_mod_checkbox)
        form.addRow("Параметр модификации (вес элитных муравьёв)", self.aco_elite_weight_input)

        self.aco_mod_checkbox.toggled.connect(self._toggle_aco_mod_settings)
        self._toggle_aco_mod_settings(self.aco_mod_checkbox.isChecked())

        self.aco_calc_button = QtWidgets.QPushButton("Рассчитать (с графикой)")
        self.aco_calc_button.clicked.connect(self.calculate_aco)
        self.aco_calc_numbers_button = QtWidgets.QPushButton("Рассчитать без графики")
        self.aco_calc_numbers_button.clicked.connect(self.calculate_aco_without_graphics)

        self.aco_path_output = QtWidgets.QPlainTextEdit()
        self.aco_path_output.setReadOnly(True)
        self.aco_path_output.setPlaceholderText("Полученный кратчайший путь (ACO)")
        self.aco_path_output.setMaximumHeight(110)

        self.aco_length_label = QtWidgets.QLabel("Длина кратчайшего пути: -")
        self.aco_report_output = QtWidgets.QPlainTextEdit()
        self.aco_report_output.setReadOnly(True)
        self.aco_report_output.setPlaceholderText("Результаты расчёта ACO")

        layout.addLayout(form)
        layout.addWidget(self.aco_calc_button)
        layout.addWidget(self.aco_calc_numbers_button)
        layout.addWidget(QtWidgets.QLabel("Кратчайший путь (номера вершин):"))
        layout.addWidget(self.aco_path_output)
        layout.addWidget(self.aco_length_label)
        layout.addWidget(QtWidgets.QLabel("Отчёт ACO:"))
        layout.addWidget(self.aco_report_output, 1)
        return panel

    def _toggle_sa_mod_settings(self, enabled: bool) -> None:
        self.sa_boltzmann_shift_input.setEnabled(enabled)

    def _toggle_aco_mod_settings(self, enabled: bool) -> None:
        self.aco_elite_weight_input.setEnabled(enabled)

    def _build_middle_panel(self) -> QtWidgets.QWidget:
        box = QtWidgets.QGroupBox("Графы")
        layout = QtWidgets.QVBoxLayout(box)

        self.input_graph = GraphCanvas("Входной граф", clickable=True, show_base_edges=True)
        self.output_graph = GraphCanvas("Выходной граф", clickable=False, show_base_edges=False)
        self.input_graph.vertex_added.connect(self.on_vertex_added)

        controls = QtWidgets.QHBoxLayout()
        self.clear_button = QtWidgets.QPushButton("Очистить")
        self.clear_button.clicked.connect(self.clear_graph)
        self.load_button = QtWidgets.QPushButton("Загрузить граф")
        self.load_button.clicked.connect(self.load_graph)
        self.load_control_button = QtWidgets.QPushButton("Загрузить тестовый пример")
        self.load_control_button.clicked.connect(self.load_control_graph)
        controls.addWidget(self.clear_button)
        controls.addWidget(self.load_button)
        controls.addWidget(self.load_control_button)
        controls.addStretch(1)

        layout.addWidget(self.input_graph)
        layout.addLayout(controls)
        layout.addWidget(self.output_graph)
        return box

    def _build_right_panel(self) -> QtWidgets.QWidget:
        box = QtWidgets.QGroupBox("Таблица рёбер")
        layout = QtWidgets.QVBoxLayout(box)

        self.table_info = QtWidgets.QLabel("")
        self.table_info.setWordWrap(True)

        self.table = QtWidgets.QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Вершина 1", "Вершина 2", "Длина", "Феромон"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.itemChanged.connect(self.on_table_item_changed)

        layout.addWidget(self.table_info)
        layout.addWidget(self.table)
        return box

    def _refresh_all_views(self) -> None:
        self.input_graph.set_graph_positions(self.graph.positions, self.graph.distances)
        self.output_graph.set_graph_positions(self.graph.positions, self.graph.distances)
        self.output_graph.set_route([])
        self._fill_table()

    def _fill_table(self) -> None:
        edges = self.graph.edge_list()
        self._table_updates_blocked = True
        try:
            self.table.blockSignals(True)
            self.table.setSortingEnabled(False)
            self.table.setUpdatesEnabled(False)
            self.table.setRowCount(len(edges))
            for r, (v1, v2, length, ph) in enumerate(edges):
                self.table.setItem(r, 0, QtWidgets.QTableWidgetItem(str(v1)))
                self.table.setItem(r, 1, QtWidgets.QTableWidgetItem(str(v2)))
                self.table.setItem(r, 2, QtWidgets.QTableWidgetItem(str(length)))
                self.table.setItem(r, 3, QtWidgets.QTableWidgetItem(str(ph)))
            self.table_info.setText(f"Рёбер: {len(edges)}")
        finally:
            self.table.setUpdatesEnabled(True)
            self.table.setSortingEnabled(True)
            self.table.blockSignals(False)
            self._table_updates_blocked = False

    def on_vertex_added(self, x: float, y: float) -> None:
        self.graph.add_vertex(x, y)
        self._refresh_all_views()
        self.statusBar().showMessage(f"Добавлена вершина {self.graph.node_count}")

    def clear_graph(self) -> None:
        self.graph = GraphData.create_empty()
        self._refresh_all_views()
        self._clear_all_algorithm_outputs()
        self.statusBar().showMessage("Граф очищен")

    def load_control_graph(self) -> None:
        self.graph = build_control_graph()
        self._refresh_all_views()
        self._clear_all_algorithm_outputs()
        self.statusBar().showMessage(f"Загружен тестовый пример: {self.graph.name}")

    def _load_cached_or_parse(self, file_path: str) -> GraphData:
        if file_path not in self._cache:
            self._cache[file_path] = parse_stp_graph(file_path)
        return self._cache[file_path].clone()

    def load_graph(self) -> None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        default = os.path.join(base_dir, "berlin52.stp")
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Выберите граф",
            default,
            "STP files (*.stp);;All files (*)",
        )
        if not file_path:
            return
        try:
            self.graph = self._load_cached_or_parse(file_path)
            self._refresh_all_views()
            self._clear_all_algorithm_outputs()
            self.statusBar().showMessage(f"Граф загружен: {self.graph.name}")
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить файл:\n{exc}")

    def on_table_item_changed(self, item: QtWidgets.QTableWidgetItem) -> None:
        if self._table_updates_blocked:
            return
        row = item.row()
        try:
            v1_item = self.table.item(row, 0)
            v2_item = self.table.item(row, 1)
            length_item = self.table.item(row, 2)
            pher_item = self.table.item(row, 3)
            if not (v1_item and v2_item and length_item and pher_item):
                return
            v1 = int(v1_item.text()) - 1
            v2 = int(v2_item.text()) - 1
            length = float(length_item.text())
            pher = float(pher_item.text())
        except Exception:
            return
        if not (0 <= v1 < self.graph.node_count and 0 <= v2 < self.graph.node_count):
            return
        if v1 == v2:
            return
        self.graph.distances[v1][v2] = max(0.000001, length)
        self.graph.pheromones[v1][v2] = max(0.0, pher)

    def _clear_all_algorithm_outputs(self) -> None:
        self.sa_path_output.clear()
        self.sa_report_output.clear()
        self.sa_length_label.setText("Длина кратчайшего пути: -")
        self.aco_path_output.clear()
        self.aco_report_output.clear()
        self.aco_length_label.setText("Длина кратчайшего пути: -")

    def _calc_sa_on_current_graph(self, use_mods: bool):
        graph = self.graph
        if graph.node_count < 3:
            raise ValueError("Добавьте минимум 3 вершины")

        n = graph.node_count
        sa_iters = self.sa_iter_input.value()
        start_temp_raw = self.sa_start_temp_input.value()
        start_temp = None if start_temp_raw <= 0 else start_temp_raw
        cooling_rate = self.sa_cooling_rate_input.value()
        boltzmann_shift = self.sa_boltzmann_shift_input.value()
        if n >= 400:
            sa_iters = max(300, sa_iters // 4)
        elif n >= 200:
            sa_iters = max(600, sa_iters // 2)

        parallel_compute = self.parallel_checkbox.isChecked()
        run_parallel = parallel_compute and n >= 40
        if run_parallel:
            with ProcessPoolExecutor(max_workers=PARALLEL_WORKERS) as executor:
                sa_res = executor.submit(
                    _solve_sa_worker,
                    graph,
                    sa_iters,
                    use_mods,
                    start_temp,
                    cooling_rate,
                    boltzmann_shift,
                ).result()
        else:
            sa_res = self.sa.solve(
                graph,
                iterations=sa_iters,
                use_boltzmann_mod=use_mods,
                start_temp=start_temp,
                cooling_rate=cooling_rate,
                boltzmann_log_shift=boltzmann_shift,
            )
        exact = exact_hamiltonian_cycle_for_small_graph(graph)
        lines = []
        lines.append(
            f"{sa_res.name}: длина={sa_res.length:.3f}, время={sa_res.elapsed_ms:.2f} ms"
        )
        lines.append(
            f"Параметры запуска: SA итерации={sa_iters}, начальная температура={'авто' if start_temp is None else f'{start_temp:.3f}'}, "
            f"коэффициент охлаждения={cooling_rate:.6f}, модификация Больцмана={'вкл' if use_mods else 'выкл'}, "
            f"параметр Больцмана={boltzmann_shift:.3f}, "
            f"параллельно={'да' if run_parallel else 'нет'}"
        )
        if exact is not None:
            lines.append(f"{exact.name}: длина={exact.length:.3f}, время={exact.elapsed_ms:.2f} ms")
        return sa_res, lines

    def _calc_aco_on_current_graph(self, use_mods: bool):
        graph = self.graph
        if graph.node_count < 3:
            raise ValueError("Добавьте минимум 3 вершины")
        alpha = self.alpha_input.value()
        beta = self.beta_input.value()
        q = self.q_input.value()
        evap_input = self.evap_input.value()
        evap = min(0.999, max(0.0, evap_input / EVAPORATION_INPUT_SCALE_FACTOR))
        ant_iters = self.aco_iter_input.value()
        ant_count = self.ant_count_input.value()
        elite_weight = self.aco_elite_weight_input.value()

        n = graph.node_count
        if n >= 400:
            ant_iters = max(1, ant_iters // 3)
        elif n >= 200:
            ant_iters = max(1, ant_iters // 2)

        parallel_compute = self.parallel_checkbox.isChecked()
        run_parallel = parallel_compute and n >= 40
        if run_parallel:
            with ProcessPoolExecutor(max_workers=PARALLEL_WORKERS) as executor:
                ac_res = executor.submit(
                    _solve_aco_worker,
                    graph,
                    ant_iters,
                    ant_count,
                    alpha,
                    beta,
                    q,
                    evap,
                    use_mods,
                    elite_weight,
                ).result()
        else:
            ac_res = self.aco.solve(
                graph,
                iterations=ant_iters,
                ant_count=ant_count,
                alpha=alpha,
                beta=beta,
                q=q,
                evaporation=evap,
                use_elite_ants_mod=use_mods,
                elite_weight=elite_weight,
            )

        exact = exact_hamiltonian_cycle_for_small_graph(graph)
        lines = [
            f"{ac_res.name}: длина={ac_res.length:.3f}, время={ac_res.elapsed_ms:.2f} ms",
            (
                f"Параметры запуска: ACO итерации={ant_iters}, муравьи={ant_count}, "
                f"испарение(ввод)={evap_input:.2f}, испарение(в алгоритме)={evap:.3f}, "
                f"модификация элитных муравьёв={'вкл' if use_mods else 'выкл'}, "
                f"вес элитных муравьёв={elite_weight:.2f}, "
                f"параллельно={'да' if run_parallel else 'нет'}"
            ),
        ]
        if exact is not None:
            lines.append(f"{exact.name}: длина={exact.length:.3f}, время={exact.elapsed_ms:.2f} ms")
        return ac_res, lines

    def _run_sa_calculation(self, with_graphics: bool) -> None:
        try:
            use_mods = self.sa_mod_checkbox.isChecked()
            best, local_lines = self._calc_sa_on_current_graph(use_mods)
            if with_graphics:
                self.sa_path_output.setPlainText(format_route(best.route))
            else:
                self.sa_path_output.setPlainText("Режим без графики: выводится только числовой отчёт")
            self.sa_length_label.setText(f"Длина кратчайшего пути: {best.length:.6f}")
            if with_graphics:
                self.output_graph.set_graph_positions(self.graph.positions, self.graph.distances)
                self.output_graph.set_route(best.route)
            else:
                self.output_graph.set_route([])

            report_lines = ["Текущий граф:", *local_lines]
            self.sa_report_output.setPlainText("\n".join(report_lines))

            self.statusBar().showMessage("Расчёт SA завершён")
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Ошибка расчёта", str(exc))

    def _run_aco_calculation(self, with_graphics: bool) -> None:
        try:
            use_mods = self.aco_mod_checkbox.isChecked()
            best, local_lines = self._calc_aco_on_current_graph(use_mods)
            if with_graphics:
                self.aco_path_output.setPlainText(format_route(best.route))
            else:
                self.aco_path_output.setPlainText("Режим без графики: выводится только числовой отчёт")
            self.aco_length_label.setText(f"Длина кратчайшего пути: {best.length:.6f}")
            if with_graphics:
                self.output_graph.set_graph_positions(self.graph.positions, self.graph.distances)
                self.output_graph.set_route(best.route)
            else:
                self.output_graph.set_route([])

            report_lines = ["Текущий граф:", *local_lines]
            self.aco_report_output.setPlainText("\n".join(report_lines))

            self.statusBar().showMessage("Расчёт ACO завершён")
        except Exception as exc:
            QtWidgets.QMessageBox.critical(self, "Ошибка расчёта", str(exc))

    def calculate_sa(self) -> None:
        self._run_sa_calculation(with_graphics=True)

    def calculate_sa_without_graphics(self) -> None:
        self._run_sa_calculation(with_graphics=False)

    def calculate_aco(self) -> None:
        self._run_aco_calculation(with_graphics=True)

    def calculate_aco_without_graphics(self) -> None:
        self._run_aco_calculation(with_graphics=False)


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
