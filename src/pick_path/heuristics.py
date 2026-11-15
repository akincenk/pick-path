"""Classic aisle-by-aisle routing heuristics for a single-block warehouse.

They are what pickers can follow without a screen: simple rules about when to cross an aisle and
when to turn back. See Roodbergen and De Koster (2001), "Routing methods for warehouses with
multiple cross aisles", for the definitions used here.
"""

from __future__ import annotations

from collections import defaultdict

from .layout import Layout
from .picks import Pick
from .routing import Route, Stop, depot


def _aisles(layout: Layout, picks: list[Pick]) -> list[list[Pick]]:
    """Picks grouped by aisle, aisles in walking order starting from the side nearest the depot."""
    groups: dict[float, list[Pick]] = defaultdict(list)
    for pick in picks:
        groups[pick.x].append(pick)
    xs = sorted(groups)
    if abs(layout.depot_x - xs[-1]) < abs(layout.depot_x - xs[0]):
        xs.reverse()
    return [sorted(groups[x], key=lambda p: p.y) for x in xs]


class _Walk:
    def __init__(self, layout: Layout):
        self.length = layout.aisle_length
        self.stops = [depot(layout)]

    def to(self, x: float, y: float) -> None:
        self.stops.append(Stop(x, y))

    def pick(self, picks: list[Pick]) -> None:
        self.stops.extend(Stop(p.x, p.y, p) for p in picks)

    def traverse(self, aisle: list[Pick], upward: bool) -> None:
        x = aisle[0].x
        self.to(x, 0.0 if upward else self.length)
        self.pick(aisle if upward else aisle[::-1])
        self.to(x, self.length if upward else 0.0)

    def dip_from_front(self, picks: list[Pick]) -> None:
        if picks:
            self.to(picks[0].x, 0.0)
            self.pick(picks)
            self.to(picks[0].x, 0.0)

    def dip_from_back(self, picks: list[Pick]) -> None:
        if picks:
            self.to(picks[0].x, self.length)
            self.pick(picks[::-1])
            self.to(picks[0].x, self.length)

    def finish(self, strategy: str, layout: Layout) -> Route:
        end = depot(layout)
        if self.stops[-1].y != 0.0:  # pragma: no cover - every heuristic ends on the front cross aisle
            raise AssertionError("route must end on the front cross aisle")
        self.stops.append(end)
        return Route(strategy, self.stops)


def s_shape(layout: Layout, picks: list[Pick]) -> Route:
    """Walk through every aisle that has a pick. With an odd number of aisles, the last one is a return trip."""
    walk = _Walk(layout)
    aisles = _aisles(layout, picks)
    for i, aisle in enumerate(aisles):
        upward = i % 2 == 0
        if upward and i == len(aisles) - 1:
            walk.dip_from_front(aisle)
        else:
            walk.traverse(aisle, upward)
    return walk.finish("s-shape", layout)


def return_route(layout: Layout, picks: list[Pick]) -> Route:
    """Enter and leave every aisle from the front."""
    walk = _Walk(layout)
    for aisle in _aisles(layout, picks):
        walk.dip_from_front(aisle)
    return walk.finish("return", layout)


def _split_route(name: str, layout: Layout, picks: list[Pick], split) -> Route:
    """Shared shape of midpoint and largest gap.

    Walk up the first aisle, along the back taking the back part of each middle aisle, down the last
    aisle, then along the front taking the front part of each middle aisle on the way home.
    """
    aisles = _aisles(layout, picks)
    if len(aisles) == 1:
        route = return_route(layout, picks)
        route.strategy = name
        return route
    walk = _Walk(layout)
    middle = [split(aisle, layout.aisle_length) for aisle in aisles[1:-1]]
    walk.traverse(aisles[0], upward=True)
    for _, back in middle:
        walk.dip_from_back(back)
    walk.traverse(aisles[-1], upward=False)
    for front, _ in reversed(middle):
        walk.dip_from_front(front)
    return walk.finish(name, layout)


def _midpoint_split(aisle: list[Pick], length: float) -> tuple[list[Pick], list[Pick]]:
    return [p for p in aisle if p.y <= length / 2], [p for p in aisle if p.y > length / 2]


def _largest_gap_split(aisle: list[Pick], length: float) -> tuple[list[Pick], list[Pick]]:
    """Split where the walk saved is largest: the biggest gap between front, picks and back is never walked."""
    ys = [0.0] + [p.y for p in aisle] + [length]
    gaps = [b - a for a, b in zip(ys, ys[1:], strict=False)]
    cut = gaps.index(max(gaps))  # picks before index ``cut`` come from the front
    return aisle[:cut], aisle[cut:]


def midpoint(layout: Layout, picks: list[Pick]) -> Route:
    return _split_route("midpoint", layout, picks, _midpoint_split)


def largest_gap(layout: Layout, picks: list[Pick]) -> Route:
    return _split_route("largest-gap", layout, picks, _largest_gap_split)
