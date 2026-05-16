import collections
import os
import sys
import time
from typing import Callable, Dict, List, Set, Tuple

import PyQt5
from PyQt5 import QtCore, QtGui, QtWidgets

from algorithms import (
    SearchResult,
    bfs_nodes_at_distance,
    bidirectional_bfs_nodes_at_distance,
    binary_lifting_nodes_at_distance,
    generate_random_binary_tree,
    lca_precompute_nodes_at_distance,
)

plugin_path = os.path.join(os.path.dirname(PyQt5.__file__), "Qt5", "plugins")
if os.path.isdir(plugin_path):
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plugin_path


MAX_DISPLAY_NODES = 40


class TreeCanvas(QtWidgets.QWidget):
    nodeClicked = QtCore.pyqtSignal(int)

    def __init__(self) -> None:
        super().__init__()
        self.setMinimumHeight(320)
        self._adjacency: Dict[int, List[int]] = {}
        self._positions: Dict[int, QtCore.QPointF] = {}
        self._target = 0
        self._highlighted: Set[int] = set()

    def set_tree(self, adjacency: Dict[int, List[int]], target: int, highlighted: List[int]) -> None:
        self._adjacency = adjacency
        self._target = target
        self._highlighted = set(highlighted)
        self._positions = self._build_positions(adjacency)
        self.update()

    def _build_positions(self, adjacency: Dict[int, List[int]]) -> Dict[int, QtCore.QPointF]:
        if not adjacency:
            return {}
        levels: Dict[int, List[int]] = {0: [0]}
        parent = {0: -1}
        queue = collections.deque([0])
        while queue:
            node = queue.popleft()
            depth = 0
            cur = node
            while parent[cur] != -1:
                cur = parent[cur]
                depth += 1
            for nxt in adjacency[node]:
                if nxt in parent:
                    continue
                parent[nxt] = node
                levels.setdefault(depth + 1, []).append(nxt)
                queue.append(nxt)
        positions: Dict[int, QtCore.QPointF] = {}
        w = max(600, self.width())
        h = max(320, self.height())
        max_depth = max(levels)
        for depth, nodes in levels.items():
            y = 40 + depth * (h - 80) / max(1, max_depth)
            step = w / (len(nodes) + 1)
            for idx, node in enumerate(nodes):
                x = (idx + 1) * step
                positions[node] = QtCore.QPointF(x, y)
        return positions

    def paintEvent(self, _: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        painter.fillRect(self.rect(), QtGui.QColor("#f8fafc"))
        if not self._adjacency or not self._positions:
            painter.drawText(self.rect(), QtCore.Qt.AlignCenter, "Сгенерируйте дерево")
            return

        edge_pen = QtGui.QPen(QtGui.QColor("#cbd5e1"))
        edge_pen.setWidth(2)
        painter.setPen(edge_pen)
        visited = set()
        for node, neighbors in self._adjacency.items():
            for nxt in neighbors:
                key = tuple(sorted((node, nxt)))
                if key in visited:
                    continue
                visited.add(key)
                painter.drawLine(self._positions[node], self._positions[nxt])

        for node, point in self._positions.items():
            if node == self._target:
                color = QtGui.QColor("#ef4444")
            elif node in self._highlighted:
                color = QtGui.QColor("#3b82f6")
            else:
                color = QtGui.QColor("#e2e8f0")
            painter.setBrush(color)
            painter.setPen(QtGui.QPen(QtGui.QColor("#0f172a")))
            painter.drawEllipse(point, 16, 16)
            painter.drawText(
                QtCore.QRectF(point.x() - 12, point.y() - 10, 24, 20),
                QtCore.Qt.AlignCenter,
                str(node),
            )

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if not self._positions:
            return
        click_pos = event.pos()
        selected_node = None
        min_dist_sq = float("inf")
        for node, pos in self._positions.items():
            dx = pos.x() - click_pos.x()
            dy = pos.y() - click_pos.y()
            dist_sq = dx * dx + dy * dy
            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq
                selected_node = node
        if selected_node is not None and min_dist_sq <= 22 * 22:
            self.nodeClicked.emit(selected_node)


def _timestamp_seed() -> int:
    return int(time.time_ns())


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Algo2/Third — Дерево и расстояние Z")
        self.resize(1180, 760)

        self.adjacency: Dict[int, List[int]] = {}

        central = QtWidgets.QWidget()
        root = QtWidgets.QVBoxLayout(central)
        self.setCentralWidget(central)

        params = QtWidgets.QGroupBox("Параметры дерева и запроса")
        form = QtWidgets.QGridLayout(params)

        self.nodes_input = QtWidgets.QSpinBox()
        self.nodes_input.setRange(10, 1000)
        self.nodes_input.setValue(50)

        self.seed_input = QtWidgets.QLineEdit(str(_timestamp_seed()))
        self.seed_input.setPlaceholderText("Введите ключ генерации (целое число)")

        self.target_input = QtWidgets.QSpinBox()
        self.target_input.setRange(0, 999)
        self.target_input.setValue(0)

        self.distance_input = QtWidgets.QSpinBox()
        self.distance_input.setRange(0, 999)
        self.distance_input.setValue(5)

        self.generate_btn = QtWidgets.QPushButton("Сгенерировать дерево")
        self.run_btn = QtWidgets.QPushButton("Запустить сравнение")
        self.seed_btn = QtWidgets.QPushButton("Новый ключ генерации")

        self.bidirectional_checkbox = QtWidgets.QCheckBox("Модификация: двунаправленный BFS")
        self.lca_checkbox = QtWidgets.QCheckBox("Модификация: LCA с предподсчетом")
        self.binary_checkbox = QtWidgets.QCheckBox("Модификация: Binary Lifting")
        self.bidirectional_checkbox.setChecked(True)
        self.lca_checkbox.setChecked(True)
        self.binary_checkbox.setChecked(True)

        form.addWidget(QtWidgets.QLabel("Число вершин N:"), 0, 0)
        form.addWidget(self.nodes_input, 0, 1)
        form.addWidget(QtWidgets.QLabel("Ключ генерации:"), 0, 2)
        form.addWidget(self.seed_input, 0, 3)
        form.addWidget(self.seed_btn, 0, 4)
        form.addWidget(QtWidgets.QLabel("Целевая вершина:"), 1, 0)
        form.addWidget(self.target_input, 1, 1)
        form.addWidget(QtWidgets.QLabel("Расстояние Z:"), 1, 2)
        form.addWidget(self.distance_input, 1, 3)
        form.addWidget(self.generate_btn, 1, 4)
        form.addWidget(self.run_btn, 1, 5)
        form.addWidget(self.bidirectional_checkbox, 2, 0, 1, 2)
        form.addWidget(self.lca_checkbox, 2, 2)
        form.addWidget(self.binary_checkbox, 2, 3)

        root.addWidget(params)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.canvas = TreeCanvas()
        splitter.addWidget(self.canvas)

        right = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right)

        self.result_table = QtWidgets.QTableWidget(0, 5)
        self.result_table.setHorizontalHeaderLabels(["Алгоритм", "Узлы", "Кол-во", "Время (мс)", "Операции"])
        self.result_table.horizontalHeader().setStretchLastSection(True)
        self.result_table.setWordWrap(True)
        right_layout.addWidget(self.result_table)

        self.summary = QtWidgets.QPlainTextEdit()
        self.summary.setReadOnly(True)
        right_layout.addWidget(self.summary)

        splitter.addWidget(right)
        splitter.setSizes([650, 520])
        root.addWidget(splitter)

        self.generate_btn.clicked.connect(self.generate_tree)
        self.run_btn.clicked.connect(self.run_search)
        self.seed_btn.clicked.connect(self.refresh_seed)
        self.target_input.valueChanged.connect(self._update_target_highlight)
        self.canvas.nodeClicked.connect(self._on_canvas_node_clicked)

        self.generate_tree()
        self._apply_style()

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow { background: #f1f5f9; }
            QGroupBox {
                font-weight: 600;
                border: 1px solid #cbd5e1;
                border-radius: 10px;
                margin-top: 12px;
                background: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }
            QPushButton {
                background: #2563eb;
                color: white;
                border-radius: 6px;
                padding: 6px 10px;
            }
            QPushButton:hover { background: #1d4ed8; }
            QTableWidget, QPlainTextEdit {
                background: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
            }
            """
        )

    def refresh_seed(self) -> None:
        self.seed_input.setText(str(_timestamp_seed()))

    def _seed_value(self) -> int:
        text = self.seed_input.text().strip()
        if text.isdigit():
            return int(text)
        seed = _timestamp_seed()
        self.seed_input.setText(str(seed))
        return seed

    def _on_canvas_node_clicked(self, node: int) -> None:
        self.target_input.setValue(node)
        self.statusBar().showMessage(f"Целевая вершина выбрана кликом: {node}", 2500)

    def _update_target_highlight(self) -> None:
        self.canvas.set_tree(self.adjacency, self.target_input.value(), [])

    def generate_tree(self) -> None:
        node_count = self.nodes_input.value()
        self.adjacency = generate_random_binary_tree(node_count, self._seed_value())
        self.target_input.setRange(0, node_count - 1)
        if self.target_input.value() >= node_count:
            self.target_input.setValue(0)
        self.distance_input.setRange(0, max(0, node_count - 1))
        self.canvas.set_tree(self.adjacency, self.target_input.value(), [])
        self.summary.setPlainText(
            f"Сгенерировано дерево из {node_count} вершин.\n"
            f"Ключ генерации: {self._seed_value()}\n"
            "Подсказка: целевую вершину можно выбрать кликом по дереву."
        )
        self.result_table.setRowCount(0)

    def _selected_algorithms(self) -> List[Tuple[str, Callable[[Dict[int, List[int]], int, int], SearchResult]]]:
        selected: List[Tuple[str, Callable[[Dict[int, List[int]], int, int], SearchResult]]] = [
            ("Базовый BFS", bfs_nodes_at_distance)
        ]
        if self.bidirectional_checkbox.isChecked():
            selected.append(("Двунаправленный BFS", bidirectional_bfs_nodes_at_distance))
        if self.lca_checkbox.isChecked():
            selected.append(("LCA предподсчет", lca_precompute_nodes_at_distance))
        if self.binary_checkbox.isChecked():
            selected.append(("Binary Lifting", binary_lifting_nodes_at_distance))
        return selected

    def run_search(self) -> None:
        if not self.adjacency:
            return
        target = self.target_input.value()
        distance = self.distance_input.value()

        rows = []
        for name, fn in self._selected_algorithms():
            result = fn(self.adjacency, target, distance)
            rows.append((name, result))

        self.result_table.setRowCount(len(rows))
        baseline_nodes = rows[0][1].nodes if rows else []
        for idx, (name, result) in enumerate(rows):
            cells = [
                name,
                ", ".join(map(str, result.nodes[:MAX_DISPLAY_NODES]))
                + (" ..." if len(result.nodes) > MAX_DISPLAY_NODES else ""),
                str(len(result.nodes)),
                f"{result.elapsed_ms:.4f}",
                str(result.operations),
            ]
            for c_idx, value in enumerate(cells):
                self.result_table.setItem(idx, c_idx, QtWidgets.QTableWidgetItem(value))
            if result.nodes != baseline_nodes:
                self.result_table.item(idx, 0).setBackground(QtGui.QColor(255, 220, 220))

        self.canvas.set_tree(self.adjacency, target, baseline_nodes)

        mismatches = [name for name, result in rows[1:] if result.nodes != baseline_nodes]
        if mismatches:
            status = f"Несовпадение результатов у: {', '.join(mismatches)}"
        else:
            status = "Все выбранные алгоритмы дают одинаковый ответ."

        self.summary.setPlainText(
            f"Цель: {target}\n"
            f"Расстояние Z: {distance}\n"
            f"Найдено вершин: {len(baseline_nodes)}\n"
            f"{status}"
        )


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
