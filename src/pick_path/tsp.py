"""Routes that treat picking as a travelling salesman problem on the aisle network."""

from __future__ import annotations

from .layout import Layout
from .picks import Pick
from .routing import Route, RouteError, Stop, depot, distance, route_from_sequence

EXACT_LIMIT = 12  # Held-Karp is O(n^2 * 2^n); 12 distinct locations stays under a second in Python.


def _locations(picks: list[Pick]) -> list[list[Pick]]:
    """Picks grouped by location so several lines in one bay cost nothing extra."""
    groups: dict[tuple[float, float], list[Pick]] = {}
    for pick in picks:
        groups.setdefault((pick.x, pick.y), []).append(pick)
    return list(groups.values())


def _matrix(layout: Layout, groups: list[list[Pick]]) -> list[list[float]]:
    points: list[Stop | Pick] = [depot(layout)] + [g[0] for g in groups]
    return [[distance(a, b, layout.aisle_length) for b in points] for a in points]


def _route(name: str, layout: Layout, groups: list[list[Pick]], order: list[int]) -> Route:
    return route_from_sequence(name, layout, [p for i in order for p in groups[i - 1]])


def _nearest_order(d: list[list[float]]) -> list[int]:
    left = set(range(1, len(d)))
    order: list[int] = []
    here = 0
    while left:
        here = min(left, key=lambda j: (d[here][j], j))
        order.append(here)
        left.remove(here)
    return order


def nearest_neighbour(layout: Layout, picks: list[Pick]) -> Route:
    """Always walk to the closest location not yet visited."""
    groups = _locations(picks)
    return _route("nearest", layout, groups, _nearest_order(_matrix(layout, groups)))


def two_opt(layout: Layout, picks: list[Pick]) -> Route:
    """Start from nearest neighbour, then reverse stretches of the tour while that shortens it."""
    groups = _locations(picks)
    d = _matrix(layout, groups)
    tour = [0, *_nearest_order(d), 0]
    improved = True
    while improved:
        improved = False
        for i in range(1, len(tour) - 2):
            for k in range(i + 1, len(tour) - 1):
                a, b, c, e = tour[i - 1], tour[i], tour[k], tour[k + 1]
                if d[a][c] + d[b][e] < d[a][b] + d[c][e] - 1e-9:
                    tour[i : k + 1] = reversed(tour[i : k + 1])
                    improved = True
    return _route("two-opt", layout, groups, tour[1:-1])


def exact(layout: Layout, picks: list[Pick], limit: int = EXACT_LIMIT) -> Route:
    """Shortest possible route (Held-Karp dynamic programming). Only for small pick lists."""
    groups = _locations(picks)
    n = len(groups)
    if n > limit:
        raise RouteError(f"exact needs {limit} or fewer distinct locations, this list has {n}")
    d = _matrix(layout, groups)
    full = (1 << n) - 1
    inf = float("inf")
    # cost[mask][j]: shortest walk from the depot through the locations in mask, ending at j.
    cost = [[inf] * n for _ in range(1 << n)]
    parent = [[-1] * n for _ in range(1 << n)]
    for j in range(n):
        cost[1 << j][j] = d[0][j + 1]
    for mask in range(1, 1 << n):
        for j in range(n):
            here = cost[mask][j]
            if here == inf or not mask >> j & 1:
                continue
            for k in range(n):
                if mask >> k & 1:
                    continue
                nxt = mask | 1 << k
                c = here + d[j + 1][k + 1]
                if c < cost[nxt][k]:
                    cost[nxt][k] = c
                    parent[nxt][k] = j
    last = min(range(n), key=lambda j: cost[full][j] + d[j + 1][0])
    order: list[int] = []
    mask = full
    while last != -1:
        order.append(last + 1)
        last, mask = parent[mask][last], mask & ~(1 << last)
    return _route("exact", layout, groups, order[::-1])
