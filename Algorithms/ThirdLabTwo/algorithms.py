import collections
import random
import time
from dataclasses import dataclass
from math import ceil, log2
from typing import Dict, List, Sequence, Set, Tuple


@dataclass
class SearchResult:
    nodes: List[int]
    elapsed_ms: float
    operations: int


def generate_random_binary_tree(node_count: int, seed: int | None = None) -> Dict[int, List[int]]:
    node_count = max(1, int(node_count))
    rng = random.Random(seed)
    adjacency: Dict[int, List[int]] = {i: [] for i in range(node_count)}
    children_count = [0] * node_count
    available_parents = [0]
    available_set = {0}

    for node in range(1, node_count):
        if not available_parents:
            available_parents = [idx for idx, count in enumerate(children_count) if count < 2]
            available_set = set(available_parents)
        parent = rng.choice(available_parents)
        adjacency[parent].append(node)
        adjacency[node].append(parent)
        children_count[parent] += 1
        if children_count[parent] >= 2 and parent in available_set:
            available_set.remove(parent)
            available_parents = [item for item in available_parents if item != parent]
        available_parents.append(node)
        available_set.add(node)
    return adjacency


def _as_sorted(result: Set[int]) -> List[int]:
    return sorted(result)


def bfs_nodes_at_distance(adjacency: Dict[int, List[int]], target: int, distance: int) -> SearchResult:
    start = time.perf_counter()
    if distance < 0 or target not in adjacency:
        return SearchResult([], 0.0, 0)

    visited = {target}
    queue = collections.deque([(target, 0)])
    result: Set[int] = set()
    operations = 0

    while queue:
        node, dist = queue.popleft()
        operations += 1
        if dist == distance:
            result.add(node)
            continue
        if dist > distance:
            continue
        for nxt in adjacency[node]:
            operations += 1
            if nxt in visited:
                continue
            visited.add(nxt)
            queue.append((nxt, dist + 1))

    elapsed = (time.perf_counter() - start) * 1000.0
    return SearchResult(_as_sorted(result), elapsed, operations)


def _bidirectional_shortest_distance(adjacency: Dict[int, List[int]], src: int, dst: int) -> Tuple[int, int]:
    if src == dst:
        return 0, 1
    q1 = collections.deque([src])
    q2 = collections.deque([dst])
    d1 = {src: 0}
    d2 = {dst: 0}
    operations = 0

    while q1 and q2:
        if len(q1) <= len(q2):
            operations += 1
            node = q1.popleft()
            for nxt in adjacency[node]:
                operations += 1
                if nxt not in d1:
                    d1[nxt] = d1[node] + 1
                    q1.append(nxt)
                    if nxt in d2:
                        return d1[nxt] + d2[nxt], operations
        else:
            operations += 1
            node = q2.popleft()
            for nxt in adjacency[node]:
                operations += 1
                if nxt not in d2:
                    d2[nxt] = d2[node] + 1
                    q2.append(nxt)
                    if nxt in d1:
                        return d1[nxt] + d2[nxt], operations
    return -1, operations


def bidirectional_bfs_nodes_at_distance(
    adjacency: Dict[int, List[int]],
    target: int,
    distance: int,
) -> SearchResult:
    start = time.perf_counter()
    if distance < 0 or target not in adjacency:
        return SearchResult([], 0.0, 0)

    nodes = []
    operations = 0
    for node in adjacency:
        dist, ops = _bidirectional_shortest_distance(adjacency, target, node)
        operations += ops
        if dist == distance:
            nodes.append(node)

    elapsed = (time.perf_counter() - start) * 1000.0
    return SearchResult(sorted(nodes), elapsed, operations)


def _build_rooted_tree(adjacency: Dict[int, List[int]], root: int = 0) -> Tuple[List[int], List[int], List[List[int]]]:
    n = len(adjacency)
    parent = [-1] * n
    depth = [0] * n
    children: List[List[int]] = [[] for _ in range(n)]

    queue = collections.deque([root])
    parent[root] = root
    while queue:
        node = queue.popleft()
        for nxt in adjacency[node]:
            if parent[nxt] != -1:
                continue
            parent[nxt] = node
            depth[nxt] = depth[node] + 1
            children[node].append(nxt)
            queue.append(nxt)
    return parent, depth, children


def _lca_naive(u: int, v: int, parent: Sequence[int], depth: Sequence[int], op_counter: List[int]) -> int:
    while depth[u] > depth[v]:
        op_counter[0] += 1
        u = parent[u]
    while depth[v] > depth[u]:
        op_counter[0] += 1
        v = parent[v]
    while u != v:
        op_counter[0] += 1
        u = parent[u]
        v = parent[v]
    return u


def lca_precompute_nodes_at_distance(
    adjacency: Dict[int, List[int]],
    target: int,
    distance: int,
    root: int = 0,
) -> SearchResult:
    start = time.perf_counter()
    if distance < 0 or target not in adjacency:
        return SearchResult([], 0.0, 0)

    parent, depth, _ = _build_rooted_tree(adjacency, root)
    ops = [len(adjacency)]
    result = []

    for node in adjacency:
        ancestor = _lca_naive(target, node, parent, depth, ops)
        dist = depth[target] + depth[node] - 2 * depth[ancestor]
        ops[0] += 1
        if dist == distance:
            result.append(node)

    elapsed = (time.perf_counter() - start) * 1000.0
    return SearchResult(sorted(result), elapsed, ops[0])


def _build_binary_lifting(parent: Sequence[int]) -> List[List[int]]:
    n = len(parent)
    max_pow = max(1, ceil(log2(max(2, n))))
    up = [[0] * n for _ in range(max_pow + 1)]
    up[0] = list(parent)
    for k in range(1, max_pow + 1):
        for v in range(n):
            up[k][v] = up[k - 1][up[k - 1][v]]
    return up


def _lca_binary(u: int, v: int, depth: Sequence[int], up: Sequence[Sequence[int]], op_counter: List[int]) -> int:
    if depth[u] < depth[v]:
        u, v = v, u
    diff = depth[u] - depth[v]
    bit = 0
    while diff:
        if diff & 1:
            op_counter[0] += 1
            u = up[bit][u]
        diff >>= 1
        bit += 1
    if u == v:
        return u
    for bit in range(len(up) - 1, -1, -1):
        op_counter[0] += 1
        if up[bit][u] != up[bit][v]:
            u = up[bit][u]
            v = up[bit][v]
    return up[0][u]


def binary_lifting_nodes_at_distance(
    adjacency: Dict[int, List[int]],
    target: int,
    distance: int,
    root: int = 0,
) -> SearchResult:
    start = time.perf_counter()
    if distance < 0 or target not in adjacency:
        return SearchResult([], 0.0, 0)

    parent, depth, _ = _build_rooted_tree(adjacency, root)
    up = _build_binary_lifting(parent)
    ops = [len(up) * len(adjacency)]
    result = []

    for node in adjacency:
        ancestor = _lca_binary(target, node, depth, up, ops)
        dist = depth[target] + depth[node] - 2 * depth[ancestor]
        ops[0] += 1
        if dist == distance:
            result.append(node)

    elapsed = (time.perf_counter() - start) * 1000.0
    return SearchResult(sorted(result), elapsed, ops[0])
