import collections
import heapq
import math
import random
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, List, Optional, Sequence, Set, Tuple


GridPoint = Tuple[int, int]
MovePath = List[GridPoint]
MAX_TIME_LIMIT_S = 1800.0


@dataclass
class SolverStats:
    found: bool
    elapsed_ms: float
    operations: int
    path: List
    note: str = ""


@dataclass
class HamiltonianOptions:
    use_warnsdorff: bool = False
    use_connectivity_pruning: bool = False
    use_backjumping: bool = False
    time_limit_s: float = MAX_TIME_LIMIT_S


MAX_HAMILTONIAN_EXACT_CELLS = 100


DIRECTIONS_4: Tuple[GridPoint, ...] = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _in_bounds(r: int, c: int, rows: int, cols: int) -> bool:
    return 0 <= r < rows and 0 <= c < cols


def _neighbors(cell: GridPoint, rows: int, cols: int) -> List[GridPoint]:
    r, c = cell
    out = []
    for dr, dc in DIRECTIONS_4:
        nr, nc = r + dr, c + dc
        if _in_bounds(nr, nc, rows, cols):
            out.append((nr, nc))
    return out


def _unvisited_connectivity_ok(
    rows: int,
    cols: int,
    visited: Set[GridPoint],
    finish: GridPoint,
) -> bool:
    free = [(r, c) for r in range(rows) for c in range(cols) if (r, c) not in visited]
    if not free:
        return True
    if finish not in visited and finish not in free:
        return False

    start = free[0]
    q = collections.deque([start])
    seen = {start}
    while q:
        node = q.popleft()
        for nxt in _neighbors(node, rows, cols):
            if nxt in visited or nxt in seen:
                continue
            seen.add(nxt)
            q.append(nxt)
    if len(seen) != len(free):
        return False
    return finish in visited or finish in seen


def _order_candidates(
    current: GridPoint,
    rows: int,
    cols: int,
    visited: Set[GridPoint],
    use_warnsdorff: bool,
) -> List[GridPoint]:
    candidates = [p for p in _neighbors(current, rows, cols) if p not in visited]
    if not use_warnsdorff:
        return candidates

    def onward_degree(cell: GridPoint) -> int:
        return sum(1 for nxt in _neighbors(cell, rows, cols) if nxt not in visited)

    return sorted(candidates, key=onward_degree)


def solve_hamiltonian_path(
    rows: int,
    cols: int,
    start: GridPoint,
    finish: GridPoint,
    options: HamiltonianOptions,
) -> SolverStats:
    begin = time.perf_counter()
    target_len = rows * cols
    if target_len > MAX_HAMILTONIAN_EXACT_CELLS:
        return SolverStats(
            False,
            0.0,
            0,
            [],
            f"Размер {rows}x{cols} слишком большой для точного перебора (>{MAX_HAMILTONIAN_EXACT_CELLS} клеток)",
        )

    if start == finish and target_len > 1:
        return SolverStats(False, 0.0, 0, [], "Старт и финиш не могут совпадать для полного пути")

    start_color = (start[0] + start[1]) % 2
    finish_color = (finish[0] + finish[1]) % 2
    if target_len % 2 == 0 and start_color == finish_color:
        return SolverStats(False, 0.0, 0, [], "Для чётного числа клеток старт и финиш должны быть разного цвета")
    if target_len % 2 == 1:
        color0 = (target_len + 1) // 2
        color1 = target_len // 2
        majority_color = 0 if color0 > color1 else 1
        if start_color != finish_color or start_color != majority_color:
            return SolverStats(False, 0.0, 0, [], "Для нечётного числа клеток старт и финиш должны быть на цвете большинства")

    visited: Set[GridPoint] = {start}
    path: MovePath = [start]
    operations = 0
    deadline = begin + max(0.1, options.time_limit_s)

    def dfs(cell: GridPoint, depth: int) -> Tuple[bool, int]:
        nonlocal operations
        if time.perf_counter() > deadline:
            return False, max(0, depth - 1)

        operations += 1
        if len(path) == target_len:
            return (cell == finish), depth

        candidates = _order_candidates(cell, rows, cols, visited, options.use_warnsdorff)
        if options.use_backjumping and len(candidates) == 0:
            return False, max(0, depth - 2)

        local_jump = depth - 1
        for nxt in candidates:
            if nxt == finish and len(path) + 1 != target_len:
                continue
            visited.add(nxt)
            path.append(nxt)

            if options.use_connectivity_pruning and not _unvisited_connectivity_ok(rows, cols, visited, finish):
                operations += 1
                path.pop()
                visited.remove(nxt)
                continue

            found, jump_target = dfs(nxt, depth + 1)
            if found:
                return True, depth

            path.pop()
            visited.remove(nxt)
            local_jump = min(local_jump, jump_target)
            if options.use_backjumping and jump_target < depth - 1:
                return False, jump_target

        return False, local_jump

    found, _ = dfs(start, 0)
    elapsed = (time.perf_counter() - begin) * 1000.0
    note = ""
    if not found and time.perf_counter() > deadline:
        note = "Прервано по лимиту времени"
    return SolverStats(found, elapsed, operations, path[:] if found else [], note)


GOAL_STATE: Tuple[int, ...] = tuple(list(range(1, 16)) + [0])
GOAL_POS: Dict[int, Tuple[int, int]] = {value: (idx // 4, idx % 4) for idx, value in enumerate(GOAL_STATE)}
PUZZLE_MOVES: Tuple[Tuple[str, int, int], ...] = (("U", -1, 0), ("D", 1, 0), ("L", 0, -1), ("R", 0, 1))
PUZZLE_REVERSE_MOVE: Dict[str, str] = {"U": "D", "D": "U", "L": "R", "R": "L"}


def _build_puzzle_transitions() -> Tuple[Tuple[Tuple[str, int], ...], ...]:
    transitions: List[List[Tuple[str, int]]] = []
    for zero in range(16):
        zr, zc = divmod(zero, 4)
        options: List[Tuple[str, int]] = []
        for code, dr, dc in PUZZLE_MOVES:
            nr, nc = zr + dr, zc + dc
            if not _in_bounds(nr, nc, 4, 4):
                continue
            options.append((code, nr * 4 + nc))
        transitions.append(options)
    return tuple(tuple(options) for options in transitions)


PUZZLE_TRANSITIONS: Tuple[Tuple[Tuple[str, int], ...], ...] = _build_puzzle_transitions()


def manhattan_distance(state: Sequence[int]) -> int:
    dist = 0
    for idx, value in enumerate(state):
        if value == 0:
            continue
        r, c = divmod(idx, 4)
        gr, gc = GOAL_POS[value]
        dist += abs(r - gr) + abs(c - gc)
    return dist


def linear_conflict(state: Sequence[int]) -> int:
    """Возвращает добавку к Manhattan-эвристике для 15-пазла.

    Для каждой строки/столбца считаются только непересекающиеся конфликты,
    чтобы штраф оставался консервативным и не переоценивал расстояние.
    """

    def max_disjoint_inversions(goal_order: List[int]) -> int:
        n = len(goal_order)
        memo: Dict[int, int] = {}

        def dfs(mask: int) -> int:
            if mask == 0:
                return 0
            if mask in memo:
                return memo[mask]

            first = (mask & -mask).bit_length() - 1
            best = dfs(mask & ~(1 << first))
            for j in range(first + 1, n):
                if not (mask & (1 << j)):
                    continue
                if goal_order[first] > goal_order[j]:
                    best = max(best, 1 + dfs(mask & ~(1 << first) & ~(1 << j)))
            memo[mask] = best
            return best

        return dfs((1 << n) - 1)

    conflict = 0

    for row in range(4):
        row_goal_cols: List[int] = []
        for col in range(4):
            value = state[row * 4 + col]
            if value == 0:
                continue
            goal_row, goal_col = GOAL_POS[value]
            if goal_row == row:
                row_goal_cols.append(goal_col)
        # Каждый линейный конфликт добавляет минимум 2 хода (вывести плитку и вернуть).
        conflict += 2 * max_disjoint_inversions(row_goal_cols)

    for col in range(4):
        col_goal_rows: List[int] = []
        for row in range(4):
            value = state[row * 4 + col]
            if value == 0:
                continue
            goal_row, goal_col = GOAL_POS[value]
            if goal_col == col:
                col_goal_rows.append(goal_row)
        # Каждый линейный конфликт добавляет минимум 2 хода (вывести плитку и вернуть).
        conflict += 2 * max_disjoint_inversions(col_goal_rows)

    return conflict


@lru_cache(maxsize=100000)
def _heuristic_distance_cached(state: Tuple[int, ...]) -> int:
    return manhattan_distance(state) + linear_conflict(state)


def heuristic_distance(state: Sequence[int]) -> int:
    return _heuristic_distance_cached(tuple(state))


def is_solvable(state: Sequence[int]) -> bool:
    arr = [x for x in state if x != 0]
    inv = 0
    for i in range(len(arr)):
        for j in range(i + 1, len(arr)):
            if arr[i] > arr[j]:
                inv += 1
    zero_row_from_bottom = 4 - (state.index(0) // 4)
    return (inv + zero_row_from_bottom) % 2 == 1


def random_solvable_state(seed: Optional[int] = None, shuffle_steps: int = 100) -> Tuple[int, ...]:
    rng = random.Random(seed)
    state = list(GOAL_STATE)
    zero = 15
    prev = -1
    for _ in range(max(1, shuffle_steps)):
        zr, zc = divmod(zero, 4)
        candidates = []
        for _, dr, dc in PUZZLE_MOVES:
            nr, nc = zr + dr, zc + dc
            if not _in_bounds(nr, nc, 4, 4):
                continue
            pos = nr * 4 + nc
            if pos == prev:
                continue
            candidates.append(pos)
        nxt = rng.choice(candidates)
        state[zero], state[nxt] = state[nxt], state[zero]
        prev, zero = zero, nxt
    return tuple(state)


def _next_states(state: Tuple[int, ...], last_move: str = "") -> List[Tuple[str, Tuple[int, ...]]]:
    zero = state.index(0)
    out: List[Tuple[str, Tuple[int, ...]]] = []
    for code, pos in PUZZLE_TRANSITIONS[zero]:
        if last_move and PUZZLE_REVERSE_MOVE[last_move] == code:
            continue
        data = list(state)
        data[zero], data[pos] = data[pos], data[zero]
        out.append((code, tuple(data)))
    return out


def _next_states_with_zero(
    state: Tuple[int, ...], zero: int, last_move: str = ""
) -> List[Tuple[str, Tuple[int, ...], int]]:
    out: List[Tuple[str, Tuple[int, ...], int]] = []
    for code, pos in PUZZLE_TRANSITIONS[zero]:
        if last_move and PUZZLE_REVERSE_MOVE[last_move] == code:
            continue
        data = list(state)
        data[zero], data[pos] = data[pos], data[zero]
        out.append((code, tuple(data), pos))
    return out


def solve_puzzle_manhattan_greedy(
    start: Tuple[int, ...], time_limit_s: float = MAX_TIME_LIMIT_S
) -> SolverStats:
    begin = time.perf_counter()
    deadline = begin + max(0.1, time_limit_s)
    state = start
    path: List[str] = []
    seen = {state}
    operations = 0
    last_move = ""

    while True:
        if time.perf_counter() > deadline:
            elapsed = (time.perf_counter() - begin) * 1000.0
            return SolverStats(False, elapsed, operations, path, "Жадный алгоритм прерван по лимиту времени")
        operations += 1
        if state == GOAL_STATE:
            elapsed = (time.perf_counter() - begin) * 1000.0
            return SolverStats(True, elapsed, operations, path)
        candidates = _next_states(state, last_move)
        if not candidates:
            break
        candidates.sort(key=lambda item: heuristic_distance(item[1]))
        chosen = None
        for move, nxt in candidates:
            if nxt not in seen:
                chosen = (move, nxt)
                break
        if chosen is None:
            chosen = candidates[0]
        move, state = chosen
        path.append(move)
        last_move = move
        seen.add(state)

    elapsed = (time.perf_counter() - begin) * 1000.0
    return SolverStats(False, elapsed, operations, path, "Жадный алгоритм не смог найти улучшающий ход")


def solve_puzzle_astar(
    start: Tuple[int, ...], max_nodes: int = 1200000, time_limit_s: float = MAX_TIME_LIMIT_S
) -> SolverStats:
    begin = time.perf_counter()
    deadline = begin + max(0.1, time_limit_s)
    if start == GOAL_STATE:
        return SolverStats(True, 0.0, 1, [])

    operations = 0
    start_zero = start.index(0)
    open_heap: List[Tuple[int, int, Tuple[int, ...], int, str]] = []
    heapq.heappush(open_heap, (heuristic_distance(start), 0, start, start_zero, ""))
    g_score: Dict[Tuple[int, ...], int] = {start: 0}
    parent: Dict[Tuple[int, ...], Tuple[Tuple[int, ...], str]] = {start: (start, "")}

    while open_heap:
        if time.perf_counter() > deadline:
            elapsed = (time.perf_counter() - begin) * 1000.0
            return SolverStats(False, elapsed, operations, [], "A* прерван по лимиту времени")
        if len(g_score) > max_nodes:
            elapsed = (time.perf_counter() - begin) * 1000.0
            return SolverStats(False, elapsed, operations, [], "A* достиг лимита состояний")

        _, g_cur, state, zero_pos, last_move = heapq.heappop(open_heap)
        if g_cur != g_score.get(state, g_cur):
            continue

        operations += 1
        if state == GOAL_STATE:
            path: List[str] = []
            cur = state
            while cur != start:
                prev, move = parent[cur]
                path.append(move)
                cur = prev
            path.reverse()
            elapsed = (time.perf_counter() - begin) * 1000.0
            return SolverStats(True, elapsed, operations, path)

        for move, nxt, next_zero in _next_states_with_zero(state, zero_pos, last_move):
            next_g = g_cur + 1
            if next_g >= g_score.get(nxt, math.inf):
                continue
            g_score[nxt] = next_g
            parent[nxt] = (state, move)
            heapq.heappush(open_heap, (next_g + heuristic_distance(nxt), next_g, nxt, next_zero, move))

    elapsed = (time.perf_counter() - begin) * 1000.0
    return SolverStats(False, elapsed, operations, [], "A* не нашел решение")


def solve_puzzle_bfs(
    start: Tuple[int, ...], time_limit_s: float = MAX_TIME_LIMIT_S
) -> SolverStats:
    begin = time.perf_counter()
    deadline = begin + max(0.1, time_limit_s)
    if start == GOAL_STATE:
        return SolverStats(True, 0.0, 1, [])

    forward_q = collections.deque([start])
    backward_q = collections.deque([GOAL_STATE])
    forward_parent: Dict[Tuple[int, ...], Tuple[Tuple[int, ...], str]] = {start: (start, "")}
    backward_parent: Dict[Tuple[int, ...], Tuple[Tuple[int, ...], str]] = {GOAL_STATE: (GOAL_STATE, "")}
    operations = 0

    meet_state: Optional[Tuple[int, ...]] = None

    while forward_q and backward_q and meet_state is None:
        if time.perf_counter() > deadline:
            elapsed = (time.perf_counter() - begin) * 1000.0
            return SolverStats(False, elapsed, operations, [], "BFS прерван по лимиту времени")

        if len(forward_q) <= len(backward_q):
            current_q = forward_q
            current_parent = forward_parent
            other_parent = backward_parent
        else:
            current_q = backward_q
            current_parent = backward_parent
            other_parent = forward_parent

        layer_size = len(current_q)
        for _ in range(layer_size):
            if time.perf_counter() > deadline:
                elapsed = (time.perf_counter() - begin) * 1000.0
                return SolverStats(False, elapsed, operations, [], "BFS прерван по лимиту времени")
            state = current_q.popleft()
            operations += 1
            last_move = current_parent[state][1]
            for move, nxt in _next_states(state, last_move):
                if nxt in current_parent:
                    continue
                current_parent[nxt] = (state, move)
                if nxt in other_parent:
                    meet_state = nxt
                    break
                current_q.append(nxt)
            if meet_state is not None:
                break

    if meet_state is None:
        elapsed = (time.perf_counter() - begin) * 1000.0
        return SolverStats(False, elapsed, operations, [], "BFS не нашел решение в заданных ограничениях")

    path_forward: List[str] = []
    cur = meet_state
    while cur != start:
        prev, move = forward_parent[cur]
        path_forward.append(move)
        cur = prev
    path_forward.reverse()

    path_backward: List[str] = []
    cur = meet_state
    while cur != GOAL_STATE:
        prev, move = backward_parent[cur]
        path_backward.append(PUZZLE_REVERSE_MOVE[move])
        cur = prev

    path = path_forward + path_backward
    elapsed = (time.perf_counter() - begin) * 1000.0
    return SolverStats(True, elapsed, operations, path)


def solve_puzzle_ida(
    start: Tuple[int, ...], max_depth_limit: int = 80, time_limit_s: float = MAX_TIME_LIMIT_S
) -> SolverStats:
    begin = time.perf_counter()
    deadline = begin + max(0.1, time_limit_s)
    operations = 0
    path: List[str] = []

    bound = heuristic_distance(start)
    if start == GOAL_STATE:
        return SolverStats(True, 0.0, 1, path)

    def search(
        state: Tuple[int, ...], g: int, bound_now: int, last_move: str, visited: Set[Tuple[int, ...]]
    ) -> Tuple[float, bool]:
        nonlocal operations
        if time.perf_counter() > deadline:
            return math.inf, False
        operations += 1
        h = heuristic_distance(state)
        f = g + h
        if f > bound_now:
            return f, False
        if state == GOAL_STATE:
            return f, True
        min_next = math.inf
        for move, nxt in _next_states(state, last_move):
            if nxt in visited:
                continue
            visited.add(nxt)
            path.append(move)
            t, done = search(nxt, g + 1, bound_now, move, visited)
            if done:
                return t, True
            if t < min_next:
                min_next = t
            path.pop()
            visited.remove(nxt)
        return min_next, False

    while bound <= max_depth_limit:
        if time.perf_counter() > deadline:
            elapsed = (time.perf_counter() - begin) * 1000.0
            return SolverStats(False, elapsed, operations, [], "IDA* прерван по лимиту времени")
        visited = {start}
        threshold, done = search(start, 0, bound, "", visited)
        if done:
            elapsed = (time.perf_counter() - begin) * 1000.0
            return SolverStats(True, elapsed, operations, path[:])
        if threshold == math.inf:
            break
        bound = threshold

    elapsed = (time.perf_counter() - begin) * 1000.0
    return SolverStats(False, elapsed, operations, [], "IDA* не нашел решение в лимите глубины")


def solve_puzzle_backjumping(
    start: Tuple[int, ...], depth_limit: int = 60, time_limit_s: float = MAX_TIME_LIMIT_S
) -> SolverStats:
    begin = time.perf_counter()
    deadline = begin + max(0.1, time_limit_s)
    operations = 0
    path: List[str] = []
    best_depth_seen: Dict[Tuple[int, ...], int] = {start: 0}

    if start == GOAL_STATE:
        return SolverStats(True, 0.0, 1, path)

    def dfs(state: Tuple[int, ...], depth: int, limit: int, last_move: str) -> Tuple[bool, int]:
        nonlocal operations
        if time.perf_counter() > deadline:
            return False, max(0, depth - 1)
        operations += 1
        h = heuristic_distance(state)
        if depth + h > limit:
            return False, max(0, depth - 1)
        if state == GOAL_STATE:
            return True, depth

        jump_target = max(0, depth - 1)
        moves = sorted(_next_states(state, last_move), key=lambda item: heuristic_distance(item[1]))
        for move, nxt in moves:
            prev_depth = best_depth_seen.get(nxt)
            if prev_depth is not None and prev_depth <= depth + 1:
                continue
            best_depth_seen[nxt] = depth + 1
            path.append(move)
            found, child_jump = dfs(nxt, depth + 1, limit, move)
            if found:
                return True, depth
            path.pop()
            jump_target = min(jump_target, child_jump)
            if child_jump < depth - 1:
                return False, child_jump
        return False, jump_target

    limit = heuristic_distance(start)
    while limit <= depth_limit:
        if time.perf_counter() > deadline:
            elapsed = (time.perf_counter() - begin) * 1000.0
            return SolverStats(False, elapsed, operations, [], "Backjumping прерван по лимиту времени")
        best_depth_seen = {start: 0}
        path.clear()
        found, _ = dfs(start, 0, limit, "")
        if found:
            elapsed = (time.perf_counter() - begin) * 1000.0
            return SolverStats(True, elapsed, operations, path[:])
        limit += 2

    elapsed = (time.perf_counter() - begin) * 1000.0
    return SolverStats(False, elapsed, operations, [], "Backjumping не нашел решение в лимите глубины")
