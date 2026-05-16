import argparse
import csv
import math
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from algorithms import (
    AntColonySolver,
    SimulatedAnnealingSolver,
    SolveResult,
    build_control_graph,
    exact_hamiltonian_cycle_for_small_graph,
    parse_stp_graph,
)

LENGTH_TOLERANCE = 1.01
LARGE_GRAPH_NODE_THRESHOLD = 600
MEDIUM_GRAPH_NODE_THRESHOLD = 50
ANT_COUNT_LARGE_GRAPH = 6
ANT_COUNT_MEDIUM_GRAPH = 24
ANT_COUNT_SMALL_GRAPH = 18


@dataclass
class ProgressReporter:
    total_steps: int
    current_step: int = 0

    def advance(self, message: str) -> None:
        self.current_step += 1
        total = max(1, self.total_steps)
        pct = min(100.0, (self.current_step / total) * 100.0)
        print(f"[{self.current_step}/{total}] {pct:6.2f}% | {message}")


@dataclass
class SAConfig:
    iterations: int
    use_mod: bool
    start_temp: Optional[float]
    cooling_rate: float
    boltzmann_shift: float


@dataclass
class ACOConfig:
    iterations: int
    use_mod: bool
    ant_count: int
    alpha: float
    beta: float
    q: float
    evaporation: float
    elite_weight: float


@dataclass
class RunEntry:
    algorithm: str
    stage: str
    graph: str
    mode: str
    iterations: int
    length: float
    elapsed_ms: float
    accuracy_gap_pct: float
    params: str


def _safe_name(name: str) -> str:
    return "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in name)


def _accuracy_gap(length: float, reference: Optional[float], best_seen: Optional[float]) -> float:
    if reference is not None and reference > 0:
        return ((length - reference) / reference) * 100.0
    if best_seen is not None and best_seen > 0:
        return ((length - best_seen) / best_seen) * 100.0
    return 0.0


def _pick_effective(entries: Sequence[RunEntry]) -> RunEntry:
    if not entries:
        raise ValueError("No run entries provided for effectiveness selection")
    best_len = min(e.length for e in entries)
    near = [e for e in entries if e.length <= best_len * LENGTH_TOLERANCE]
    if near:
        return min(near, key=lambda e: e.elapsed_ms)
    return min(entries, key=lambda e: (e.length, e.elapsed_ms))


def _parse_params_map(params: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not params.strip():
        return out
    for token in params.split(","):
        token = token.strip()
        if not token:
            continue
        if "=" not in token:
            raise ValueError(f"Malformed params token: {token}")
        k, v = token.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def _run_sa(graph, cfg: SAConfig, seed: int = 42) -> SolveResult:
    solver = SimulatedAnnealingSolver(seed=seed)
    return solver.solve(
        graph,
        iterations=cfg.iterations,
        use_boltzmann_mod=cfg.use_mod,
        start_temp=cfg.start_temp,
        cooling_rate=cfg.cooling_rate,
        boltzmann_log_shift=cfg.boltzmann_shift,
    )


def _run_aco(graph, cfg: ACOConfig, seed: int = 42) -> SolveResult:
    solver = AntColonySolver(seed=seed)
    return solver.solve(
        graph,
        iterations=cfg.iterations,
        ant_count=cfg.ant_count,
        alpha=cfg.alpha,
        beta=cfg.beta,
        q=cfg.q,
        evaporation=cfg.evaporation,
        use_elite_ants_mod=cfg.use_mod,
        elite_weight=cfg.elite_weight,
    )


def _plot_iterations(graph_name: str, algorithm: str, entries: Sequence[RunEntry], out_dir: str) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
    modes = sorted(set(e.mode for e in entries))
    for mode in modes:
        data = sorted([e for e in entries if e.mode == mode], key=lambda x: x.iterations)
        x = [d.iterations for d in data]
        y_len = [d.length for d in data]
        y_time = [d.elapsed_ms for d in data]
        axes[0].plot(x, y_len, marker="o", label=mode)
        axes[1].plot(x, y_time, marker="o", label=mode)
    axes[0].set_ylabel("Длина пути")
    axes[1].set_ylabel("Время, ms")
    axes[1].set_xlabel("Кол-во операций/итераций")
    axes[0].grid(True, alpha=0.3)
    axes[1].grid(True, alpha=0.3)
    axes[0].legend()
    axes[1].legend()
    fig.suptitle(f"{graph_name}: {algorithm} — поиск лучшего кол-ва операций")
    fig.tight_layout()
    path = os.path.join(out_dir, f"{_safe_name(graph_name)}_{algorithm}_iterations.png")
    fig.savefig(path, dpi=160)
    plt.close(fig)


def _plot_param_scan(graph_name: str, algorithm: str, entries: Sequence[RunEntry], out_dir: str) -> None:
    data = sorted(entries, key=lambda e: (e.mode, e.length, e.elapsed_ms))
    x = list(range(len(data)))
    y_len = [d.length for d in data]
    y_time = [d.elapsed_ms for d in data]
    colors = ["tab:green" if d.mode == "mod_on" else "tab:blue" for d in data]
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    axes[0].bar(x, y_len, color=colors, alpha=0.8)
    axes[1].bar(x, y_time, color=colors, alpha=0.8)
    axes[0].set_ylabel("Длина пути")
    axes[1].set_ylabel("Время, ms")
    axes[1].set_xlabel("Кандидаты параметров")
    axes[0].grid(True, alpha=0.3)
    axes[1].grid(True, alpha=0.3)
    legend_handles = [
        Patch(facecolor="tab:green", label="mod_on (с модификацией)"),
        Patch(facecolor="tab:blue", label="mod_off (без модификации)"),
    ]
    axes[0].legend(handles=legend_handles, loc="best")
    axes[1].legend(handles=legend_handles, loc="best")
    fig.suptitle(f"{graph_name}: {algorithm} — подбор коэффициентов")
    fig.tight_layout()
    path = os.path.join(out_dir, f"{_safe_name(graph_name)}_{algorithm}_params.png")
    fig.savefig(path, dpi=160)
    plt.close(fig)


def _plot_variants(graph_name: str, rows: Sequence[Tuple[str, SolveResult, SolveResult]], out_dir: str, suffix: str) -> None:
    labels = [r[0] for r in rows]
    sa_len = [r[1].length for r in rows]
    ac_len = [r[2].length for r in rows]
    sa_time = [r[1].elapsed_ms for r in rows]
    ac_time = [r[2].elapsed_ms for r in rows]
    x = list(range(len(labels)))
    w = 0.38

    fig, axes = plt.subplots(2, 1, figsize=(12, 9), sharex=True)
    axes[0].bar([i - w / 2 for i in x], sa_len, width=w, label="SA")
    axes[0].bar([i + w / 2 for i in x], ac_len, width=w, label="ACO")
    axes[0].set_ylabel("Длина пути")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    axes[1].bar([i - w / 2 for i in x], sa_time, width=w, label="SA")
    axes[1].bar([i + w / 2 for i in x], ac_time, width=w, label="ACO")
    axes[1].set_ylabel("Время, ms")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(labels, rotation=15)
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    fig.suptitle(f"{graph_name}: режимы модификаций/комбинаций/без модификаций")
    fig.tight_layout()
    path = os.path.join(out_dir, f"{_safe_name(graph_name)}_variants_{suffix}.png")
    fig.savefig(path, dpi=160)
    plt.close(fig)


def _write_csv(path: str, entries: Sequence[RunEntry]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "algorithm",
                "stage",
                "graph",
                "mode",
                "iterations",
                "length",
                "elapsed_ms",
                "accuracy_gap_pct",
                "params",
            ]
        )
        for e in entries:
            writer.writerow(
                [
                    e.algorithm,
                    e.stage,
                    e.graph,
                    e.mode,
                    e.iterations,
                    f"{e.length:.6f}",
                    f"{e.elapsed_ms:.6f}",
                    f"{e.accuracy_gap_pct:.6f}",
                    e.params,
                ]
            )


def _default_ant_count(node_count: int) -> int:
    if node_count >= LARGE_GRAPH_NODE_THRESHOLD:
        return ANT_COUNT_LARGE_GRAPH
    if node_count >= MEDIUM_GRAPH_NODE_THRESHOLD:
        return ANT_COUNT_MEDIUM_GRAPH
    return ANT_COUNT_SMALL_GRAPH


def _optimize_sa(
    graph_name: str,
    graph,
    reference: Optional[float],
    iteration_grid: Sequence[int],
    out_dir: str,
    progress: Optional[ProgressReporter] = None,
) -> Tuple[SAConfig, SAConfig, List[RunEntry]]:
    entries: List[RunEntry] = []
    defaults = {
        "start_temp": None,
        "cooling_rate": 0.997,
        "boltzmann_shift": 2.0,
    }
    best_seen = math.inf
    for mode in (False, True):
        for iterations in iteration_grid:
            cfg = SAConfig(
                iterations=iterations,
                use_mod=mode,
                start_temp=defaults["start_temp"],
                cooling_rate=defaults["cooling_rate"],
                boltzmann_shift=defaults["boltzmann_shift"],
            )
            if progress is not None:
                progress.advance(f"{graph_name} SA iterations: mode={'on' if mode else 'off'} iter={iterations}")
            res = _run_sa(graph, cfg)
            best_seen = min(best_seen, res.length)
            entries.append(
                RunEntry(
                    algorithm="SA",
                    stage="iterations",
                    graph=graph_name,
                    mode="mod_on" if mode else "mod_off",
                    iterations=iterations,
                    length=res.length,
                    elapsed_ms=res.elapsed_ms,
                    accuracy_gap_pct=0.0,
                    params=f"start_temp=auto,cooling={cfg.cooling_rate},shift={cfg.boltzmann_shift}",
                )
            )
    for e in entries:
        e.accuracy_gap_pct = _accuracy_gap(e.length, reference, best_seen)
    _plot_iterations(graph_name, "SA", entries, out_dir)

    best_iter_off = _pick_effective([e for e in entries if e.mode == "mod_off"]).iterations
    best_iter_on = _pick_effective([e for e in entries if e.mode == "mod_on"]).iterations

    param_entries: List[RunEntry] = []
    start_temps = [None, 50.0, 150.0]
    cooling_rates = [0.995, 0.997, 0.999]
    shifts = [1.5, 2.0, 3.0]
    best_seen_params = math.inf
    for mode, best_iter in ((False, best_iter_off), (True, best_iter_on)):
        mode_shifts = shifts if mode else [2.0]
        for st in start_temps:
            for cr in cooling_rates:
                for shift in mode_shifts:
                    cfg = SAConfig(
                        iterations=best_iter,
                        use_mod=mode,
                        start_temp=st,
                        cooling_rate=cr,
                        boltzmann_shift=shift,
                    )
                    if progress is not None:
                        progress.advance(
                            f"{graph_name} SA params: mode={'on' if mode else 'off'} iter={best_iter} temp={'auto' if st is None else st} cool={cr} shift={shift}"
                        )
                    res = _run_sa(graph, cfg)
                    best_seen_params = min(best_seen_params, res.length)
                    param_entries.append(
                        RunEntry(
                            algorithm="SA",
                            stage="params",
                            graph=graph_name,
                            mode="mod_on" if mode else "mod_off",
                            iterations=best_iter,
                            length=res.length,
                            elapsed_ms=res.elapsed_ms,
                            accuracy_gap_pct=0.0,
                            params=f"start_temp={'auto' if st is None else st},cooling={cr},shift={shift}",
                        )
                    )
    for e in param_entries:
        e.accuracy_gap_pct = _accuracy_gap(e.length, reference, best_seen_params)
    _plot_param_scan(graph_name, "SA", param_entries, out_dir)

    best_off = _pick_effective([e for e in param_entries if e.mode == "mod_off"])
    best_on = _pick_effective([e for e in param_entries if e.mode == "mod_on"])

    def parse_sa_params(entry: RunEntry) -> SAConfig:
        parts = _parse_params_map(entry.params)
        start_temp_raw = parts.get("start_temp", "auto")
        st = None if start_temp_raw == "auto" else float(start_temp_raw)
        return SAConfig(
            iterations=entry.iterations,
            use_mod=(entry.mode == "mod_on"),
            start_temp=st,
            cooling_rate=float(parts.get("cooling", "0.997")),
            boltzmann_shift=float(parts.get("shift", "2.0")),
        )

    return parse_sa_params(best_off), parse_sa_params(best_on), entries + param_entries


def _optimize_aco(
    graph_name: str,
    graph,
    reference: Optional[float],
    iteration_grid: Sequence[int],
    out_dir: str,
    progress: Optional[ProgressReporter] = None,
) -> Tuple[ACOConfig, ACOConfig, List[RunEntry]]:
    entries: List[RunEntry] = []
    ant_count = _default_ant_count(graph.node_count)
    defaults = {
        "alpha": 1.0,
        "beta": 3.0,
        "q": 100.0,
        "evaporation": 0.35,
        "elite_weight": 5.0,
    }
    best_seen = math.inf
    for mode in (False, True):
        for iterations in iteration_grid:
            cfg = ACOConfig(
                iterations=iterations,
                use_mod=mode,
                ant_count=ant_count,
                alpha=defaults["alpha"],
                beta=defaults["beta"],
                q=defaults["q"],
                evaporation=defaults["evaporation"],
                elite_weight=defaults["elite_weight"],
            )
            if progress is not None:
                progress.advance(f"{graph_name} ACO iterations: mode={'on' if mode else 'off'} iter={iterations}")
            res = _run_aco(graph, cfg)
            best_seen = min(best_seen, res.length)
            entries.append(
                RunEntry(
                    algorithm="ACO",
                    stage="iterations",
                    graph=graph_name,
                    mode="mod_on" if mode else "mod_off",
                    iterations=iterations,
                    length=res.length,
                    elapsed_ms=res.elapsed_ms,
                    accuracy_gap_pct=0.0,
                    params=f"ants={ant_count},alpha={cfg.alpha},beta={cfg.beta},q={cfg.q},evap={cfg.evaporation},elite={cfg.elite_weight}",
                )
            )
    for e in entries:
        e.accuracy_gap_pct = _accuracy_gap(e.length, reference, best_seen)
    _plot_iterations(graph_name, "ACO", entries, out_dir)

    best_iter_off = _pick_effective([e for e in entries if e.mode == "mod_off"]).iterations
    best_iter_on = _pick_effective([e for e in entries if e.mode == "mod_on"]).iterations

    param_entries: List[RunEntry] = []
    alphas = [0.9, 1.0, 1.2]
    betas = [2.5, 3.0, 4.0]
    qs = [80.0, 100.0]
    evaps = [0.25, 0.35, 0.5]
    elites = [4.0, 6.0]
    best_seen_params = math.inf
    for mode, best_iter in ((False, best_iter_off), (True, best_iter_on)):
        mode_elites = elites if mode else [5.0]
        for a in alphas:
            for b in betas:
                for q in qs:
                    for ev in evaps:
                        for ew in mode_elites:
                            cfg = ACOConfig(
                                iterations=best_iter,
                                use_mod=mode,
                                ant_count=ant_count,
                                alpha=a,
                                beta=b,
                                q=q,
                                evaporation=ev,
                                elite_weight=ew,
                            )
                            if progress is not None:
                                progress.advance(
                                    f"{graph_name} ACO params: mode={'on' if mode else 'off'} iter={best_iter} alpha={a} beta={b} q={q} evap={ev} elite={ew}"
                                )
                            res = _run_aco(graph, cfg)
                            best_seen_params = min(best_seen_params, res.length)
                            param_entries.append(
                                RunEntry(
                                    algorithm="ACO",
                                    stage="params",
                                    graph=graph_name,
                                    mode="mod_on" if mode else "mod_off",
                                    iterations=best_iter,
                                    length=res.length,
                                    elapsed_ms=res.elapsed_ms,
                                    accuracy_gap_pct=0.0,
                                    params=f"ants={ant_count},alpha={a},beta={b},q={q},evap={ev},elite={ew}",
                                )
                            )
    for e in param_entries:
        e.accuracy_gap_pct = _accuracy_gap(e.length, reference, best_seen_params)
    _plot_param_scan(graph_name, "ACO", param_entries, out_dir)

    best_off = _pick_effective([e for e in param_entries if e.mode == "mod_off"])
    best_on = _pick_effective([e for e in param_entries if e.mode == "mod_on"])

    def parse_aco_params(entry: RunEntry) -> ACOConfig:
        parts = _parse_params_map(entry.params)
        return ACOConfig(
            iterations=entry.iterations,
            use_mod=(entry.mode == "mod_on"),
            ant_count=int(parts.get("ants", "18")),
            alpha=float(parts.get("alpha", "1.0")),
            beta=float(parts.get("beta", "3.0")),
            q=float(parts.get("q", "100.0")),
            evaporation=float(parts.get("evap", "0.35")),
            elite_weight=float(parts.get("elite", "5.0")),
        )

    return parse_aco_params(best_off), parse_aco_params(best_on), entries + param_entries


def _run_variants(
    graph_name: str,
    graph,
    sa_off: SAConfig,
    sa_on: SAConfig,
    aco_off: ACOConfig,
    aco_on: ACOConfig,
    out_dir: str,
    suffix: str,
    progress: Optional[ProgressReporter] = None,
) -> List[RunEntry]:
    variants = [
        ("без_модификаций", sa_off, aco_off),
        ("комбинация_SA_mod", sa_on, aco_off),
        ("комбинация_ACO_mod", sa_off, aco_on),
        ("с_модификациями", sa_on, aco_on),
    ]
    rows: List[Tuple[str, SolveResult, SolveResult]] = []
    entries: List[RunEntry] = []
    for name, sa_cfg, aco_cfg in variants:
        if progress is not None:
            progress.advance(f"{graph_name} variants: {name} -> SA run")
        sa_res = _run_sa(graph, sa_cfg)
        if progress is not None:
            progress.advance(f"{graph_name} variants: {name} -> ACO run")
        ac_res = _run_aco(graph, aco_cfg)
        rows.append((name, sa_res, ac_res))
        entries.append(
            RunEntry(
                algorithm="SA",
                stage="variants",
                graph=graph_name,
                mode=name,
                iterations=sa_cfg.iterations,
                length=sa_res.length,
                elapsed_ms=sa_res.elapsed_ms,
                accuracy_gap_pct=0.0,
                params=f"start_temp={'auto' if sa_cfg.start_temp is None else sa_cfg.start_temp},cooling={sa_cfg.cooling_rate},shift={sa_cfg.boltzmann_shift},mod={sa_cfg.use_mod}",
            )
        )
        entries.append(
            RunEntry(
                algorithm="ACO",
                stage="variants",
                graph=graph_name,
                mode=name,
                iterations=aco_cfg.iterations,
                length=ac_res.length,
                elapsed_ms=ac_res.elapsed_ms,
                accuracy_gap_pct=0.0,
                params=f"ants={aco_cfg.ant_count},alpha={aco_cfg.alpha},beta={aco_cfg.beta},q={aco_cfg.q},evap={aco_cfg.evaporation},elite={aco_cfg.elite_weight},mod={aco_cfg.use_mod}",
            )
        )
    _plot_variants(graph_name, rows, out_dir, suffix=suffix)
    return entries


def _run_world_three_launches(
    world_graph,
    out_dir: str,
    defaults_sa: SAConfig,
    defaults_aco: ACOConfig,
    control_sa: SAConfig,
    control_aco: ACOConfig,
    berlin_sa: SAConfig,
    berlin_aco: ACOConfig,
    progress: Optional[ProgressReporter] = None,
) -> List[RunEntry]:
    rows: List[Tuple[str, SolveResult, SolveResult]] = []
    collected: List[RunEntry] = []
    launches = [
        ("world666_default", defaults_sa, defaults_aco),
        ("world666_control_coeffs", control_sa, control_aco),
        ("world666_berlin52_coeffs", berlin_sa, berlin_aco),
    ]
    for launch_name, sa_cfg, aco_cfg in launches:
        if progress is not None:
            progress.advance(f"{launch_name}: SA run (эквивалент кнопки Рассчитать)")
        sa_res = _run_sa(world_graph, sa_cfg)
        if progress is not None:
            progress.advance(f"{launch_name}: ACO run (эквивалент кнопки Рассчитать)")
        aco_res = _run_aco(world_graph, aco_cfg)
        rows.append((launch_name, sa_res, aco_res))
        collected.append(
            RunEntry(
                algorithm="SA",
                stage="world666_three_launches",
                graph="world666",
                mode=launch_name,
                iterations=sa_cfg.iterations,
                length=sa_res.length,
                elapsed_ms=sa_res.elapsed_ms,
                accuracy_gap_pct=0.0,
                params=f"start_temp={'auto' if sa_cfg.start_temp is None else sa_cfg.start_temp},cooling={sa_cfg.cooling_rate},shift={sa_cfg.boltzmann_shift},mod={sa_cfg.use_mod}",
            )
        )
        collected.append(
            RunEntry(
                algorithm="ACO",
                stage="world666_three_launches",
                graph="world666",
                mode=launch_name,
                iterations=aco_cfg.iterations,
                length=aco_res.length,
                elapsed_ms=aco_res.elapsed_ms,
                accuracy_gap_pct=0.0,
                params=f"ants={aco_cfg.ant_count},alpha={aco_cfg.alpha},beta={aco_cfg.beta},q={aco_cfg.q},evap={aco_cfg.evaporation},elite={aco_cfg.elite_weight},mod={aco_cfg.use_mod}",
            )
        )
    _plot_variants("world666", rows, out_dir, suffix="three_launches")
    return collected


def main() -> None:
    parser = argparse.ArgumentParser(description="Автоматический подбор SA/ACO и построение графиков")
    parser.add_argument("--output-dir", default=None, help="Папка для сохранения графиков и таблиц")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    out_dir = args.output_dir or os.path.join(base_dir, "test_outputs")
    os.makedirs(out_dir, exist_ok=True)

    control_graph = build_control_graph()
    berlin_graph = parse_stp_graph(os.path.join(base_dir, "berlin52.stp"))
    world_graph = parse_stp_graph(os.path.join(base_dir, "world666.stp"))

    control_exact = exact_hamiltonian_cycle_for_small_graph(control_graph)
    control_ref = control_exact.length if control_exact is not None else None
    berlin_ref = 7542.0
    total_steps = 0
    total_steps += (2 * 9 + 36) + (2 * 9 + 162) + 8  # control
    total_steps += (2 * 11 + 36) + (2 * 11 + 162) + 8  # berlin52
    total_steps += 6  # world666: 3 launches * (SA+ACO)
    progress = ProgressReporter(total_steps=total_steps)

    all_entries: List[RunEntry] = []

    sa_control_off, sa_control_on, control_sa_entries = _optimize_sa(
        graph_name="control",
        graph=control_graph,
        reference=control_ref,
        iteration_grid=[60, 120, 200, 320, 500, 750, 1100, 1500, 1900],
        out_dir=out_dir,
        progress=progress,
    )
    aco_control_off, aco_control_on, control_aco_entries = _optimize_aco(
        graph_name="control",
        graph=control_graph,
        reference=control_ref,
        iteration_grid=[8, 14, 22, 32, 45, 60, 78, 100, 130],
        out_dir=out_dir,
        progress=progress,
    )
    all_entries.extend(control_sa_entries)
    all_entries.extend(control_aco_entries)
    all_entries.extend(
        _run_variants(
            "control",
            control_graph,
            sa_control_off,
            sa_control_on,
            aco_control_off,
            aco_control_on,
            out_dir,
            suffix="optimized",
            progress=progress,
        )
    )

    sa_berlin_off, sa_berlin_on, berlin_sa_entries = _optimize_sa(
        graph_name="berlin52",
        graph=berlin_graph,
        reference=berlin_ref,
        iteration_grid=[300, 500, 800, 1100, 1500, 2000, 2600, 3300, 4100, 4600, 5000],
        out_dir=out_dir,
        progress=progress,
    )
    aco_berlin_off, aco_berlin_on, berlin_aco_entries = _optimize_aco(
        graph_name="berlin52",
        graph=berlin_graph,
        reference=berlin_ref,
        iteration_grid=[20, 30, 45, 60, 80, 105, 135, 170, 210, 260, 320],
        out_dir=out_dir,
        progress=progress,
    )
    all_entries.extend(berlin_sa_entries)
    all_entries.extend(berlin_aco_entries)
    all_entries.extend(
        _run_variants(
            "berlin52",
            berlin_graph,
            sa_berlin_off,
            sa_berlin_on,
            aco_berlin_off,
            aco_berlin_on,
            out_dir,
            suffix="optimized",
            progress=progress,
        )
    )

    defaults_sa = SAConfig(iterations=220, use_mod=True, start_temp=None, cooling_rate=0.997, boltzmann_shift=2.0)
    defaults_aco = ACOConfig(
        iterations=8,
        use_mod=True,
        ant_count=6,
        alpha=1.0,
        beta=3.0,
        q=100.0,
        evaporation=0.35,
        elite_weight=5.0,
    )
    control_world_sa = SAConfig(
        iterations=max(220, sa_control_on.iterations),
        use_mod=sa_control_on.use_mod,
        start_temp=sa_control_on.start_temp,
        cooling_rate=sa_control_on.cooling_rate,
        boltzmann_shift=sa_control_on.boltzmann_shift,
    )
    control_world_aco = ACOConfig(
        iterations=max(8, aco_control_on.iterations),
        use_mod=aco_control_on.use_mod,
        ant_count=6,
        alpha=aco_control_on.alpha,
        beta=aco_control_on.beta,
        q=aco_control_on.q,
        evaporation=aco_control_on.evaporation,
        elite_weight=aco_control_on.elite_weight,
    )
    berlin_world_sa = SAConfig(
        iterations=max(220, sa_berlin_on.iterations),
        use_mod=sa_berlin_on.use_mod,
        start_temp=sa_berlin_on.start_temp,
        cooling_rate=sa_berlin_on.cooling_rate,
        boltzmann_shift=sa_berlin_on.boltzmann_shift,
    )
    berlin_world_aco = ACOConfig(
        iterations=max(8, aco_berlin_on.iterations),
        use_mod=aco_berlin_on.use_mod,
        ant_count=6,
        alpha=aco_berlin_on.alpha,
        beta=aco_berlin_on.beta,
        q=aco_berlin_on.q,
        evaporation=aco_berlin_on.evaporation,
        elite_weight=aco_berlin_on.elite_weight,
    )
    all_entries.extend(
        _run_world_three_launches(
            world_graph=world_graph,
            out_dir=out_dir,
            defaults_sa=defaults_sa,
            defaults_aco=defaults_aco,
            control_sa=control_world_sa,
            control_aco=control_world_aco,
            berlin_sa=berlin_world_sa,
            berlin_aco=berlin_world_aco,
            progress=progress,
        )
    )

    _write_csv(os.path.join(out_dir, "results.csv"), all_entries)
    print(f"Готово. Сохранено файлов: {len(os.listdir(out_dir))} в {out_dir}")


if __name__ == "__main__":
    main()
