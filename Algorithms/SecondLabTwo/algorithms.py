import math
import random
import time
from dataclasses import dataclass
from itertools import permutations
from typing import Dict, List, Optional, Sequence, Tuple

INF = 10**18
BOLTZMANN_LOG_SHIFT = 2.0


@dataclass
class GraphData:
    name: str
    node_count: int
    distances: List[List[float]]
    pheromones: List[List[float]]
    positions: Dict[int, Tuple[float, float]]

    @staticmethod
    def create_empty(name: str = "Пользовательский граф") -> "GraphData":
        return GraphData(name=name, node_count=0, distances=[], pheromones=[], positions={})

    def clone(self) -> "GraphData":
        return GraphData(
            name=self.name,
            node_count=self.node_count,
            distances=[row[:] for row in self.distances],
            pheromones=[row[:] for row in self.pheromones],
            positions=dict(self.positions),
        )

    def add_vertex(self, x: float, y: float) -> None:
        idx = self.node_count
        self.node_count += 1
        self.positions[idx] = (x, y)
        for row in self.distances:
            row.append(INF)
        for row in self.pheromones:
            row.append(0.0)
        self.distances.append([INF] * self.node_count)
        self.pheromones.append([0.0] * self.node_count)
        self.distances[idx][idx] = 0.0
        self.pheromones[idx][idx] = 0.0
        for j in range(idx):
            x2, y2 = self.positions[j]
            d = max(1.0, round(math.hypot(x - x2, y - y2), 3))
            self.distances[idx][j] = d
            self.distances[j][idx] = d
            self.pheromones[idx][j] = 1.0
            self.pheromones[j][idx] = 1.0

    def clear(self) -> None:
        self.node_count = 0
        self.distances = []
        self.pheromones = []
        self.positions = {}

    def edge_list(self) -> List[Tuple[int, int, float, float]]:
        result: List[Tuple[int, int, float, float]] = []
        for i in range(self.node_count):
            for j in range(self.node_count):
                if i == j:
                    continue
                d = self.distances[i][j]
                if d >= INF:
                    continue
                result.append((i + 1, j + 1, d, self.pheromones[i][j]))
        return result


def build_control_graph() -> GraphData:
    positions = {
        0: (80.0, 80.0),    # A
        1: (220.0, 70.0),   # B
        2: (340.0, 170.0),  # C
        3: (250.0, 300.0),  # D
        4: (90.0, 300.0),   # F
        5: (220.0, 170.0),  # G
    }
    n = len(positions)
    distances = [[INF] * n for _ in range(n)]
    pheromones = [[0.0] * n for _ in range(n)]
    for i in range(n):
        distances[i][i] = 0.0

    def set_arc(src: int, dst: int, weight: float) -> None:
        distances[src][dst] = float(weight)
        pheromones[src][dst] = 1.0

    # Обозначения: A=0, B=1, C=2, D=3, F=4, G=5 (в условии вершина E отсутствует).
    # По условию контрольного примера (взвешенный орграф, рис.1).
    for a, b in [
        (0, 1),  # ab
        (1, 0),  # ba
        (1, 5),  # bg
        (5, 1),  # gb
        (5, 0),  # ga
        (4, 0),  # fa
        (4, 3),  # fd
        (5, 2),  # gc
    ]:
        set_arc(a, b, 3.0)

    for a, b in [
        (2, 5),  # cg
        (2, 3),  # cd
        (3, 4),  # df
        (0, 4),  # af
    ]:
        set_arc(a, b, 1.0)

    set_arc(5, 3, 5.0)  # gd
    set_arc(5, 4, 4.0)  # gf
    set_arc(3, 2, 8.0)  # dc

    return GraphData(name="Контрольный взвешенный орграф (рис.1)", node_count=n, distances=distances, pheromones=pheromones, positions=positions)


def _build_spread_positions(node_count: int) -> Dict[int, Tuple[float, float]]:
    positions: Dict[int, Tuple[float, float]] = {}
    cols = max(1, int(math.sqrt(max(1, node_count))))
    step_x = 30.0
    step_y = 24.0
    for i in range(node_count):
        col = i % cols
        row = i // cols
        positions[i] = (40.0 + col * step_x, 40.0 + row * step_y)
    return positions


def parse_stp_graph(path: str) -> GraphData:
    name = path.split("/")[-1]
    node_count = 0
    undirected_edges: List[Tuple[int, int, float]] = []
    directed_arcs: List[Tuple[int, int, float]] = []
    positions: Dict[int, Tuple[float, float]] = {}
    in_coordinates = False
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            if line.startswith("Section Coordinates"):
                in_coordinates = True
                continue
            if line == "End":
                in_coordinates = False
                continue
            if in_coordinates and line.startswith("DD "):
                parts = line.split()
                if len(parts) >= 4:
                    idx = int(parts[1]) - 1
                    x = float(parts[2])
                    y = float(parts[3])
                    positions[idx] = (x, y)
                continue
            if line.startswith("Name"):
                parts = line.split('"')
                if len(parts) >= 2:
                    name = parts[1]
                continue
            if line.startswith("Nodes"):
                node_count = int(line.split()[1])
                continue
            if line.startswith("E "):
                _, a, b, w = line.split()[:4]
                undirected_edges.append((int(a) - 1, int(b) - 1, float(w)))
                continue
            if line.startswith("A "):
                _, a, b, w = line.split()[:4]
                directed_arcs.append((int(a) - 1, int(b) - 1, float(w)))
    if node_count <= 0:
        raise ValueError(f"Не удалось прочитать узлы из файла: {path}")
    distances = [[INF] * node_count for _ in range(node_count)]
    pheromones = [[0.0] * node_count for _ in range(node_count)]
    for i in range(node_count):
        distances[i][i] = 0.0
    for i, j, w in undirected_edges:
        distances[i][j] = w
        pheromones[i][j] = 1.0
        distances[j][i] = w
        pheromones[j][i] = 1.0
    for i, j, w in directed_arcs:
        distances[i][j] = w
        pheromones[i][j] = 1.0
    if len(positions) != node_count:
        fallback = _build_spread_positions(node_count)
        missing = set(range(node_count)) - set(positions.keys())
        for idx in missing:
            positions[idx] = fallback[idx]
    return GraphData(
        name=name,
        node_count=node_count,
        distances=distances,
        pheromones=pheromones,
        positions=positions,
    )


def path_length(graph: GraphData, route: Sequence[int]) -> float:
    if not route:
        return INF
    total = 0.0
    for i in range(len(route) - 1):
        d = graph.distances[route[i]][route[i + 1]]
        if d >= INF:
            return INF
        total += d
    return total


def nearest_neighbor_route(graph: GraphData, start: int = 0) -> List[int]:
    n = graph.node_count
    if n == 0:
        return []
    unvisited = set(range(n))
    route = [start]
    unvisited.remove(start)
    cur = start
    while unvisited:
        nxt = min(unvisited, key=lambda x: graph.distances[cur][x])
        route.append(nxt)
        unvisited.remove(nxt)
        cur = nxt
    route.append(start)
    return route


def two_opt_swap(route: Sequence[int], i: int, j: int) -> List[int]:
    return list(route[:i]) + list(reversed(route[i:j])) + list(route[j:])


@dataclass
class SolveResult:
    name: str
    route: List[int]
    length: float
    elapsed_ms: float


class SimulatedAnnealingSolver:
    def __init__(self, seed: Optional[int] = None) -> None:
        self._rng = random.Random(seed)

    def solve(
        self,
        graph: GraphData,
        iterations: int,
        use_boltzmann_mod: bool = False,
        start_temp: Optional[float] = None,
        cooling_rate: float = 0.997,
        boltzmann_log_shift: float = BOLTZMANN_LOG_SHIFT,
    ) -> SolveResult:
        t0 = time.perf_counter()
        if graph.node_count < 3:
            route = list(range(graph.node_count))
            if route:
                route.append(route[0])
            return SolveResult("Имитация отжига", route, path_length(graph, route), (time.perf_counter() - t0) * 1000.0)

        cur = nearest_neighbor_route(graph, 0)
        best = cur[:]
        cur_len = path_length(graph, cur)
        best_len = cur_len

        if start_temp is None:
            finite = [
                graph.distances[i][j]
                for i in range(graph.node_count)
                for j in range(graph.node_count)
                if i != j and graph.distances[i][j] < INF
            ]
            avg = sum(finite) / max(1, len(finite)) if finite else 100.0
            start_temp = max(1.0, avg)

        temp = start_temp
        boltzmann_shift = max(1e-6, float(boltzmann_log_shift))
        for step in range(1, max(1, iterations) + 1):
            i, j = sorted(self._rng.sample(range(1, graph.node_count), 2))
            cand = two_opt_swap(cur, i, j)
            cand_len = path_length(graph, cand)
            if cand_len >= INF:
                continue
            delta = cand_len - cur_len
            accepted = False
            if delta <= 0:
                accepted = True
            else:
                denom_t = temp
                if use_boltzmann_mod:
                    denom_t = max(1e-9, start_temp / math.log(step + boltzmann_shift))
                if self._rng.random() < math.exp(-delta / max(1e-9, denom_t)):
                    accepted = True
            if accepted:
                cur = cand
                cur_len = cand_len
                if cur_len < best_len:
                    best = cur[:]
                    best_len = cur_len
            if not use_boltzmann_mod:
                temp = max(1e-9, temp * cooling_rate)

        return SolveResult(
            "Имитация отжига (Больцман)" if use_boltzmann_mod else "Имитация отжига",
            best,
            best_len,
            (time.perf_counter() - t0) * 1000.0,
        )


class AntColonySolver:
    def __init__(self, seed: Optional[int] = None) -> None:
        self._rng = random.Random(seed)

    def _select_next(
        self,
        graph: GraphData,
        pher: List[List[float]],
        cur: int,
        unvisited: Sequence[int],
        alpha: float,
        beta: float,
    ) -> int:
        scores = []
        total = 0.0
        for j in unvisited:
            d = graph.distances[cur][j]
            if d >= INF:
                continue
            p = max(1e-9, pher[cur][j]) ** alpha if alpha != 0 else 1.0
            h = (1.0 / max(1e-9, d)) ** beta if beta != 0 else 1.0
            val = p * h
            scores.append((j, val))
            total += val
        if not scores:
            return unvisited[0]
        if total <= 0:
            return self._rng.choice(list(unvisited))
        pick = self._rng.random() * total
        acc = 0.0
        for node, score in scores:
            acc += score
            if acc >= pick:
                return node
        return scores[-1][0]

    def _build_ant_route(
        self,
        graph: GraphData,
        pher: List[List[float]],
        alpha: float,
        beta: float,
    ) -> List[int]:
        n = graph.node_count
        start = self._rng.randrange(n)
        route = [start]
        unvisited = set(range(n))
        unvisited.remove(start)
        cur = start
        while unvisited:
            nxt = self._select_next(graph, pher, cur, list(unvisited), alpha, beta)
            route.append(nxt)
            unvisited.remove(nxt)
            cur = nxt
        route.append(start)
        return route

    def solve(
        self,
        graph: GraphData,
        iterations: int,
        ant_count: int,
        alpha: float,
        beta: float,
        q: float,
        evaporation: float,
        use_elite_ants_mod: bool = False,
        elite_weight: float = 5.0,
    ) -> SolveResult:
        t0 = time.perf_counter()
        n = graph.node_count
        if n < 3:
            route = list(range(n))
            if route:
                route.append(route[0])
            return SolveResult("Муравьиный алгоритм", route, path_length(graph, route), (time.perf_counter() - t0) * 1000.0)

        pher = [row[:] for row in graph.pheromones]
        for i in range(n):
            for j in range(n):
                if i != j and graph.distances[i][j] < INF and pher[i][j] <= 0:
                    pher[i][j] = 1.0

        best_route = nearest_neighbor_route(graph, 0)
        best_len = path_length(graph, best_route)

        for _ in range(max(1, iterations)):
            ant_routes: List[Tuple[List[int], float]] = []
            for _ant in range(max(1, ant_count)):
                route = self._build_ant_route(graph, pher, alpha, beta)
                plen = path_length(graph, route)
                ant_routes.append((route, plen))
                if plen < best_len:
                    best_route = route
                    best_len = plen

            evap = min(0.999, max(0.0, evaporation))
            for i in range(n):
                for j in range(n):
                    if i != j:
                        pher[i][j] *= (1.0 - evap)

            for route, plen in ant_routes:
                if plen >= INF:
                    continue
                delta = q / max(1e-9, plen)
                for i in range(len(route) - 1):
                    a, b = route[i], route[i + 1]
                    pher[a][b] += delta

            if use_elite_ants_mod and best_len < INF:
                bonus = elite_weight * q / max(1e-9, best_len)
                for i in range(len(best_route) - 1):
                    a, b = best_route[i], best_route[i + 1]
                    pher[a][b] += bonus

        return SolveResult(
            "Муравьиный алгоритм (элитные муравьи)" if use_elite_ants_mod else "Муравьиный алгоритм",
            best_route,
            best_len,
            (time.perf_counter() - t0) * 1000.0,
        )


def format_route(route: Sequence[int]) -> str:
    if not route:
        return "-"
    return " -> ".join(str(v + 1) for v in route)


def exact_hamiltonian_cycle_for_small_graph(graph: GraphData, max_nodes: int = 10) -> Optional[SolveResult]:
    if graph.node_count <= 2 or graph.node_count > max_nodes:
        return None
    t0 = time.perf_counter()
    nodes = list(range(1, graph.node_count))
    best_route: Optional[List[int]] = None
    best_len = INF
    for perm in permutations(nodes):
        route = [0, *perm, 0]
        plen = path_length(graph, route)
        if plen < best_len:
            best_len = plen
            best_route = route
    if best_route is None:
        return None
    return SolveResult("Точный перебор", best_route, best_len, (time.perf_counter() - t0) * 1000.0)


def benchmark_suite(
    small_graph: GraphData,
    berlin_graph: GraphData,
    world_graph: GraphData,
    alpha: float,
    beta: float,
    q: float,
    evaporation: float,
    with_mods: bool,
    seed: int = 42,
) -> List[Tuple[str, SolveResult, SolveResult]]:
    sa = SimulatedAnnealingSolver(seed=seed)
    ac = AntColonySolver(seed=seed)

    settings = [
        ("Малый (контрольный)", small_graph, 2200, 90, 18),
        ("Средний (berlin52)", berlin_graph, 3800, 130, 24),
        ("Большой (world666)", world_graph, 1400, 8, 6),
    ]

    rows: List[Tuple[str, SolveResult, SolveResult]] = []
    for title, graph, sa_iters, ac_iters, ants in settings:
        sa_res = sa.solve(graph, iterations=sa_iters, use_boltzmann_mod=with_mods)
        ac_res = ac.solve(
            graph,
            iterations=ac_iters,
            ant_count=ants,
            alpha=alpha,
            beta=beta,
            q=q,
            evaporation=evaporation,
            use_elite_ants_mod=with_mods,
        )
        rows.append((title, sa_res, ac_res))
    return rows
