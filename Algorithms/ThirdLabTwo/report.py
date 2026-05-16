import argparse
import csv
import os
from dataclasses import dataclass
from typing import Callable, Dict, List, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from algorithms import (
    SearchResult,
    bfs_nodes_at_distance,
    bidirectional_bfs_nodes_at_distance,
    binary_lifting_nodes_at_distance,
    generate_random_binary_tree,
    lca_precompute_nodes_at_distance,
)


@dataclass
class BenchmarkRow:
    algorithm: str
    n: int
    z: int
    target: int
    seed: int
    elapsed_ms: float
    operations: int
    nodes_count: int
    mismatch: bool


ALGORITHMS: List[Tuple[str, Callable[[Dict[int, List[int]], int, int], SearchResult]]] = [
    ("Basic BFS", bfs_nodes_at_distance),
    ("TwoWays BFS", bidirectional_bfs_nodes_at_distance),
    ("LCA", lca_precompute_nodes_at_distance),
    ("Binary Lifting", binary_lifting_nodes_at_distance),
]

DEFAULT_Z_VALUES = [1, 5, 10, 20]


def _safe_name(name: str) -> str:
    return "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in name)


def _parse_int_list(value: str) -> List[int]:
    return [int(item) for item in value.split(",") if item.strip()]


def _build_sizes(min_n: int, max_n: int, step: int) -> List[int]:
    if min_n <= 0:
        raise ValueError("min_n must be positive")
    if max_n < min_n:
        raise ValueError("max_n must be >= min_n")
    if step <= 0:
        raise ValueError("step must be positive")
    return list(range(min_n, max_n + 1, step))


def _write_csv(rows: List[BenchmarkRow], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "algorithm",
                "n",
                "z",
                "target",
                "seed",
                "elapsed_ms",
                "operations",
                "iterations",  # Добавлено поле в шапку таблицы
                "nodes_count",
                "mismatch",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row.algorithm,
                    row.n,
                    row.z,
                    row.target,
                    row.seed,
                    f"{row.elapsed_ms:.6f}",
                    row.operations,
                    row.operations,  # Количество итераций совпадает со счетчиком операций
                    row.nodes_count,
                    "yes" if row.mismatch else "no",
                ]
            )


def _plot_times(
    series: Dict[str, Dict[int, List[Tuple[int, float]]]],
    z_values: List[int],
    out_dir: str,
) -> None:
    # Настройки стилей, чтобы перекрывающиеся линии были видны
    markers = {1: "o", 5: "s", 10: "^", 20: "D"}
    widths = {1: 5.0, 5: 3.5, 10: 2.0, 20: 1.0}
    jitters = {1: -1.5, 5: -0.5, 10: 0.5, 20: 1.5}

    for algorithm, z_map in series.items():
        fig, ax = plt.subplots(figsize=(10, 6))
        for z in z_values:
            data = sorted(z_map.get(z, []), key=lambda item: item[0])
            if not data:
                continue
            
            # Добавляем небольшой сдвиг по оси X (jitter), чтобы маркеры не сливались
            shift = jitters.get(z, 0.0)
            x = [item[0] + shift for item in data]
            y = [item[1] for item in data]
            
            ax.plot(
                x, 
                y, 
                marker=markers.get(z, "o"), 
                linewidth=widths.get(z, 1.5), 
                label=f"Z={z}",
                alpha=0.9
            )
            
        ax.set_xlabel("Размерность N")
        ax.set_ylabel("Время, мс")
        ax.set_title(f"{algorithm}: время от N при разных Z")
        ax.grid(True, alpha=0.3)
        ax.legend()
        fig.tight_layout()
        fig.savefig(os.path.join(out_dir, f"{_safe_name(algorithm)}_time.png"), dpi=160)
        plt.close(fig)


def _plot_operations(
    series_ops: Dict[str, Dict[int, List[Tuple[int, int]]]],
    z_values: List[int],
    out_dir: str,
) -> None:
    # Настройки стилей для разделения линий операций
    markers = {1: "o", 5: "s", 10: "^", 20: "D"}
    widths = {1: 5.0, 5: 3.5, 10: 2.0, 20: 1.0}
    jitters = {1: -1.5, 5: -0.5, 10: 0.5, 20: 1.5}

    for algorithm, z_map in series_ops.items():
        fig, ax = plt.subplots(figsize=(10, 6))
        for z in z_values:
            data = sorted(z_map.get(z, []), key=lambda item: item[0])
            if not data:
                continue
                
            shift = jitters.get(z, 0.0)
            x = [item[0] + shift for item in data]
            y = [item[1] for item in data]
            
            ax.plot(
                x, 
                y, 
                marker=markers.get(z, "o"), 
                linestyle="--",
                linewidth=widths.get(z, 1.5), 
                label=f"Z={z}",
                alpha=0.9
            )
            
        ax.set_xlabel("Размерность N")
        ax.set_ylabel("Количество операций / итераций")
        ax.set_title(f"{algorithm}: трудоемкость (операции) от N при разных Z")
        ax.grid(True, alpha=0.3)
        ax.legend()
        fig.tight_layout()
        fig.savefig(os.path.join(out_dir, f"{_safe_name(algorithm)}_operations.png"), dpi=160)
        plt.close(fig)


def run_report(args: argparse.Namespace) -> None:
    sizes = _build_sizes(args.min_n, args.max_n, args.step)
    z_values = args.z_values
    if isinstance(z_values, str):
        z_values = _parse_int_list(z_values)
    if not z_values:
        raise ValueError("z_values list is empty")
    out_dir = args.out_dir
    os.makedirs(out_dir, exist_ok=True)

    rows: List[BenchmarkRow] = []
    series_time: Dict[str, Dict[int, List[Tuple[int, float]]]] = {
        name: {z: [] for z in z_values} for name, _ in ALGORITHMS
    }
    series_ops: Dict[str, Dict[int, List[Tuple[int, int]]]] = {
        name: {z: [] for z in z_values} for name, _ in ALGORITHMS
    }

    total_steps = len(sizes) * len(z_values)
    current_step = 0
    for n in sizes:
        seed = args.seed + n
        adjacency = generate_random_binary_tree(n, seed)
        target = min(max(args.target, 0), n - 1)
        for z in z_values:
            baseline_nodes: List[int] | None = None
            for idx, (name, fn) in enumerate(ALGORITHMS):
                result = fn(adjacency, target, z)
                if idx == 0:
                    baseline_nodes = result.nodes
                mismatch = baseline_nodes is not None and result.nodes != baseline_nodes
                rows.append(
                    BenchmarkRow(
                        algorithm=name,
                        n=n,
                        z=z,
                        target=target,
                        seed=seed,
                        elapsed_ms=result.elapsed_ms,
                        operations=result.operations,
                        nodes_count=len(result.nodes),
                        mismatch=mismatch,
                    )
                )
                series_time[name][z].append((n, result.elapsed_ms))
                series_ops[name][z].append((n, result.operations))
            current_step += 1
            print(f"[{current_step}/{total_steps}] N={n} Z={z} готовы")

    csv_path = os.path.join(out_dir, "эффективность.csv")
    _write_csv(rows, csv_path)

    if not args.skip_plots:
        _plot_times(series_time, z_values, out_dir)
        _plot_operations(series_ops, z_values, out_dir)

    print(f"Готово. CSV: {csv_path}")
    if not args.skip_plots:
        print(f"Графики сохранены в: {out_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Генерация данных для отчёта Algo2/Third (N=10..1000, Z=1/5/10/20)."
    )
    parser.add_argument("--min-n", type=int, default=10, help="Минимальная размерность дерева.")
    parser.add_argument("--max-n", type=int, default=1000, help="Максимальная размерность дерева.")
    parser.add_argument("--step", type=int, default=10, help="Шаг по размерности.")
    parser.add_argument(
        "--z-values",
        type=_parse_int_list,
        default="1,5,10,20",
        help="Список Z через запятую.",
    )
    parser.add_argument("--seed", type=int, default=42, help="Базовый seed генератора.")
    parser.add_argument("--target", type=int, default=0, help="Целевая вершина.")
    parser.add_argument(
        "--out-dir",
        default=os.path.join(os.path.dirname(__file__), "report_output"),
        help="Папка для CSV и графиков.",
    )
    parser.add_argument(
        "--skip-plots",
        action="store_true",
        help="Не строить графики (только CSV).",
    )
    args = parser.parse_args()
    run_report(args)


if __name__ == "__main__":
    main()
