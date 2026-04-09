import os
import sys
from typing import Iterable, Sequence, Tuple

import PyQt5
from PyQt5 import QtCore, QtGui, QtWidgets

from algorithms import (
    GeneticOptimizer,
    ObjectiveFn,
    SwarmConstrictionOptimizer,
    build_quadratic_objective,
)


plugin_path = os.path.join(os.path.dirname(PyQt5.__file__), "Qt5", "plugins")
if os.path.isdir(plugin_path):
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plugin_path


class FunctionEditor(QtWidgets.QGroupBox):
    def __init__(self) -> None:
        super().__init__("Редактирование функции f(x,y)")
        layout = QtWidgets.QHBoxLayout(self)

        self.a_input = QtWidgets.QDoubleSpinBox()
        self.a_input.setRange(-10.0, 10.0)
        self.a_input.setValue(0.26)
        self.a_input.setSingleStep(0.01)

        self.b_input = QtWidgets.QDoubleSpinBox()
        self.b_input.setRange(-10.0, 10.0)
        self.b_input.setValue(-0.48)
        self.b_input.setSingleStep(0.01)

        self.c_input = QtWidgets.QDoubleSpinBox()
        self.c_input.setRange(-100.0, 100.0)
        self.c_input.setValue(0.0)
        self.c_input.setSingleStep(0.1)

        self.apply_button = QtWidgets.QPushButton("Применить функцию")

        layout.addWidget(QtWidgets.QLabel("a (x²+y²):"))
        layout.addWidget(self.a_input)
        layout.addWidget(QtWidgets.QLabel("b (xy):"))
        layout.addWidget(self.b_input)
        layout.addWidget(QtWidgets.QLabel("c:"))
        layout.addWidget(self.c_input)
        layout.addWidget(self.apply_button)

    def coeffs(self) -> Sequence[float]:
        return self.a_input.value(), self.b_input.value(), self.c_input.value()


class CoordinatePlane(QtWidgets.QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.points = []
        self.setMinimumHeight(420)

    def set_points(self, points: Iterable[Sequence[float]]) -> None:
        self.points = list(points)
        self.update()

    def _to_pixel(self, x: float, y: float, width: int, height: int) -> Tuple[float, float]:
        scale_x = width / 20.0
        scale_y = height / 20.0
        px = (x + 10.0) * scale_x
        py = height - (y + 10.0) * scale_y
        return px, py

    def paintEvent(self, _: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        painter.fillRect(self.rect(), QtGui.QColor("white"))
        w = self.width()
        h = self.height()

        pen_grid = QtGui.QPen(QtGui.QColor(230, 230, 230))
        painter.setPen(pen_grid)
        for i in range(0, 21, 2):
            x = int(i * w / 20)
            y = int(i * h / 20)
            painter.drawLine(x, 0, x, h)
            painter.drawLine(0, y, w, y)

        pen_axis = QtGui.QPen(QtGui.QColor("black"))
        pen_axis.setWidth(2)
        painter.setPen(pen_axis)
        zx, zy = self._to_pixel(0.0, 0.0, w, h)
        painter.drawLine(int(zx), 0, int(zx), h)
        painter.drawLine(0, int(zy), w, int(zy))

        point_pen = QtGui.QPen(QtGui.QColor(20, 90, 200))
        point_pen.setWidth(5)
        painter.setPen(point_pen)
        for _, x, y, *_ in self.points:
            px, py = self._to_pixel(x, y, w, h)
            painter.drawPoint(int(px), int(py))


class BasePanel(QtWidgets.QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)

        self.form = QtWidgets.QFormLayout()
        layout.addLayout(self.form)

        controls = QtWidgets.QHBoxLayout()
        self.iterations_input = QtWidgets.QSpinBox()
        self.iterations_input.setRange(1, 10000)
        self.iterations_input.setValue(10)

        self.start_button = QtWidgets.QPushButton("Старт")
        self.step_button = QtWidgets.QPushButton("Старт на шаг")
        self.reset_button = QtWidgets.QPushButton("Перезагрузка")

        controls.addWidget(QtWidgets.QLabel("Итераций:"))
        controls.addWidget(self.iterations_input)
        controls.addWidget(self.start_button)
        controls.addWidget(self.step_button)
        controls.addWidget(self.reset_button)
        layout.addLayout(controls)

        self.iteration_label = QtWidgets.QLabel("Итерация: 0")
        self.best_label = QtWidgets.QLabel("Лучшее значение: -")
        layout.addWidget(self.iteration_label)
        layout.addWidget(self.best_label)

    def set_iteration(self, value: int) -> None:
        self.iteration_label.setText(f"Итерация: {value}")

    def set_best(self, value: float, best_iteration: int) -> None:
        self.best_label.setText(f"Лучшее значение: {value:.6f} (итерация: {best_iteration})")


class GeneticPanel(BasePanel):
    def __init__(self) -> None:
        super().__init__()

        self.crossover_rate = QtWidgets.QDoubleSpinBox()
        self.crossover_rate.setRange(0.0, 1.0)
        self.crossover_rate.setValue(0.8)
        self.crossover_rate.setSingleStep(0.05)

        self.mutation_rate = QtWidgets.QDoubleSpinBox()
        self.mutation_rate.setRange(0.0, 1.0)
        self.mutation_rate.setValue(0.2)
        self.mutation_rate.setSingleStep(0.05)

        self.mutation_scale = QtWidgets.QDoubleSpinBox()
        self.mutation_scale.setRange(0.01, 10.0)
        self.mutation_scale.setValue(0.6)
        self.mutation_scale.setSingleStep(0.05)

        self.elite_fraction = QtWidgets.QDoubleSpinBox()
        self.elite_fraction.setRange(0.0, 0.9)
        self.elite_fraction.setValue(0.3)
        self.elite_fraction.setSingleStep(0.05)

        self.tournament_size = QtWidgets.QSpinBox()
        self.tournament_size.setRange(2, 20)
        self.tournament_size.setValue(3)

        self.population_size = QtWidgets.QSpinBox()
        self.population_size.setRange(5, 200)
        self.population_size.setValue(20)

        self.use_new_population_mod = QtWidgets.QCheckBox("Включить модификацию 'новая популяция'")
        self.use_new_population_mod.setChecked(True)

        self.form.addRow("Вероятность скрещивания", self.crossover_rate)
        self.form.addRow("Вероятность мутации", self.mutation_rate)
        self.form.addRow("Сила мутации", self.mutation_scale)
        self.form.addRow("Доля элиты", self.elite_fraction)
        self.form.addRow("Размер турнира", self.tournament_size)
        self.form.addRow("Размер популяции", self.population_size)
        self.form.addRow("Модификация популяции", self.use_new_population_mod)

        self.plane = CoordinatePlane()
        self.layout().addWidget(self.plane)


class SwarmPanel(BasePanel):
    def __init__(self) -> None:
        super().__init__()

        self.c1 = QtWidgets.QDoubleSpinBox()
        self.c1.setRange(0.0, 5.0)
        self.c1.setValue(2.05)
        self.c1.setSingleStep(0.05)

        self.c2 = QtWidgets.QDoubleSpinBox()
        self.c2.setRange(0.0, 5.0)
        self.c2.setValue(2.05)
        self.c2.setSingleStep(0.05)

        self.inertia = QtWidgets.QDoubleSpinBox()
        self.inertia.setRange(0.0, 2.0)
        self.inertia.setValue(0.7)
        self.inertia.setSingleStep(0.05)

        self.velocity_limit = QtWidgets.QDoubleSpinBox()
        self.velocity_limit.setRange(0.01, 20.0)
        self.velocity_limit.setValue(2.0)
        self.velocity_limit.setSingleStep(0.1)

        self.neighborhood_pull = QtWidgets.QDoubleSpinBox()
        self.neighborhood_pull.setRange(0.0, 5.0)
        self.neighborhood_pull.setValue(0.0)
        self.neighborhood_pull.setSingleStep(0.05)

        self.swarm_size = QtWidgets.QSpinBox()
        self.swarm_size.setRange(5, 200)
        self.swarm_size.setValue(20)

        self.use_constriction_mod = QtWidgets.QCheckBox("Включить модификацию 'Коэффициент сжатия'")
        self.use_constriction_mod.setChecked(True)

        self.form.addRow("C1 (личный вес)", self.c1)
        self.form.addRow("C2 (глобальный вес)", self.c2)
        self.form.addRow("Инерция", self.inertia)
        self.form.addRow("Ограничение скорости", self.velocity_limit)
        self.form.addRow("Притяжение к центру", self.neighborhood_pull)
        self.form.addRow("Размер роя", self.swarm_size)
        self.form.addRow("Модификация сжатия", self.use_constriction_mod)

        self.table = QtWidgets.QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["№", "x", "y", "f(x,y)", "vx", "vy"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.layout().addWidget(self.table)

    def fill_table(self, rows: Iterable[Sequence[float]]) -> None:
        rows = list(rows)
        self.table.setRowCount(len(rows))
        for r_idx, row in enumerate(rows):
            for c_idx, value in enumerate(row):
                text = f"{value:.6f}" if isinstance(value, float) else str(value)
                self.table.setItem(r_idx, c_idx, QtWidgets.QTableWidgetItem(text))


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Algo2: Генетический и роевой алгоритм")
        self.resize(1250, 800)

        self.objective = build_quadratic_objective(0.26, -0.48, 0.0)
        self.genetic_optimizer = GeneticOptimizer(self.objective)
        self.swarm_optimizer = SwarmConstrictionOptimizer(self.objective)

        central = QtWidgets.QWidget()
        root_layout = QtWidgets.QVBoxLayout(central)

        self.function_editor = FunctionEditor()
        self.function_editor.apply_button.clicked.connect(self.apply_function)
        root_layout.addWidget(self.function_editor)

        self.tabs = QtWidgets.QTabWidget()
        self.genetic_panel = GeneticPanel()
        self.swarm_panel = SwarmPanel()
        self.tabs.addTab(self.genetic_panel, "Генетический")
        self.tabs.addTab(self.swarm_panel, "Роевой")
        root_layout.addWidget(self.tabs)

        self.setCentralWidget(central)

        self.genetic_panel.start_button.clicked.connect(self.run_genetic_batch)
        self.genetic_panel.step_button.clicked.connect(self.run_genetic_step)
        self.genetic_panel.reset_button.clicked.connect(self.reset_genetic)

        self.swarm_panel.start_button.clicked.connect(self.run_swarm_batch)
        self.swarm_panel.step_button.clicked.connect(self.run_swarm_step)
        self.swarm_panel.reset_button.clicked.connect(self.reset_swarm)

        self._refresh_genetic_view()
        self._refresh_swarm_view()
        self.statusBar().showMessage("Готово")

    def _build_objective(self) -> ObjectiveFn:
        a, b, c = self.function_editor.coeffs()
        return build_quadratic_objective(a, b, c)

    def apply_function(self) -> None:
        self.objective = self._build_objective()
        self.genetic_optimizer.set_objective(self.objective)
        self.swarm_optimizer.set_objective(self.objective)
        self._refresh_genetic_view()
        self._refresh_swarm_view()
        self.statusBar().showMessage("Функция обновлена")

    def _reset_genetic_if_population_changed(self) -> None:
        if self.genetic_optimizer.population_size != self.genetic_panel.population_size.value():
            self.genetic_optimizer.population_size = self.genetic_panel.population_size.value()
            self.genetic_optimizer.reset()

    def _reset_swarm_if_size_changed(self) -> None:
        if self.swarm_optimizer.swarm_size != self.swarm_panel.swarm_size.value():
            self.swarm_optimizer.swarm_size = self.swarm_panel.swarm_size.value()
            self.swarm_optimizer.reset()

    def _refresh_genetic_view(self) -> None:
        rows = [
            (idx + 1, c.x, c.y, c.value, c.fitness)
            for idx, c in enumerate(self.genetic_optimizer.population)
        ]
        self.genetic_panel.plane.set_points(rows)
        self.genetic_panel.set_iteration(self.genetic_optimizer.iteration)
        self.genetic_panel.set_best(self.genetic_optimizer.best_value, self.genetic_optimizer.best_iteration)

    def _refresh_swarm_view(self) -> None:
        rows = [
            (idx + 1, p.x, p.y, self.objective(p.x, p.y), p.vx, p.vy)
            for idx, p in enumerate(self.swarm_optimizer.swarm)
        ]
        self.swarm_panel.fill_table(rows)
        self.swarm_panel.set_iteration(self.swarm_optimizer.iteration)
        self.swarm_panel.set_best(self.swarm_optimizer.global_best[2], self.swarm_optimizer.global_best_iteration)

    def run_genetic_step(self) -> None:
        self._reset_genetic_if_population_changed()
        self.genetic_optimizer.set_parameters(
            self.genetic_panel.crossover_rate.value(),
            self.genetic_panel.mutation_rate.value(),
            self.genetic_panel.mutation_scale.value(),
            self.genetic_panel.elite_fraction.value(),
            self.genetic_panel.tournament_size.value(),
            self.genetic_panel.use_new_population_mod.isChecked(),
        )
        self.genetic_optimizer.step()
        self._refresh_genetic_view()

    def run_genetic_batch(self) -> None:
        count = self.genetic_panel.iterations_input.value()
        for _ in range(count):
            self.run_genetic_step()

    def reset_genetic(self) -> None:
        self.genetic_optimizer.population_size = self.genetic_panel.population_size.value()
        self.genetic_optimizer.reset()
        self._refresh_genetic_view()

    def run_swarm_step(self) -> None:
        self._reset_swarm_if_size_changed()
        self.swarm_optimizer.set_parameters(
            self.swarm_panel.c1.value(),
            self.swarm_panel.c2.value(),
            self.swarm_panel.inertia.value(),
            self.swarm_panel.velocity_limit.value(),
            self.swarm_panel.neighborhood_pull.value(),
            self.swarm_panel.use_constriction_mod.isChecked(),
        )
        rows = self.swarm_optimizer.step()
        self.swarm_panel.fill_table(rows)
        self.swarm_panel.set_iteration(self.swarm_optimizer.iteration)
        self.swarm_panel.set_best(self.swarm_optimizer.global_best[2], self.swarm_optimizer.global_best_iteration)

    def run_swarm_batch(self) -> None:
        count = self.swarm_panel.iterations_input.value()
        for _ in range(count):
            self.run_swarm_step()

    def reset_swarm(self) -> None:
        self.swarm_optimizer.swarm_size = self.swarm_panel.swarm_size.value()
        self.swarm_optimizer.reset()
        self._refresh_swarm_view()


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
