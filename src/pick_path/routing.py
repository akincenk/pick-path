"""Walking distance in the aisle network and the Route type every strategy returns."""

from __future__ import annotations

import math
from dataclasses import dataclass

from .layout import Layout
from .picks import Pick


class RouteError(ValueError):
    """A route cannot be built (for example too many locations for the exact solver)."""


@dataclass(frozen=True)
class Stop:
    """A point the picker walks through. ``pick`` is set when an item is picked here."""

    x: float
    y: float
    pick: Pick | None = None


@dataclass
class Route:
    strategy: str
    stops: list[Stop]

    @property
    def distance(self) -> float:
        return sum(abs(a.x - b.x) + abs(a.y - b.y) for a, b in zip(self.stops, self.stops[1:], strict=False))

    @property
    def picks(self) -> list[Pick]:
        return [s.pick for s in self.stops if s.pick is not None]

    def visits(self) -> list[tuple[Pick, float]]:
        """Each pick with the distance walked from the depot when it is reached."""
        walked = 0.0
        out: list[tuple[Pick, float]] = []
        for prev, stop in zip(self.stops, self.stops[1:], strict=False):
            walked += abs(prev.x - stop.x) + abs(prev.y - stop.y)
            if stop.pick is not None:
                out.append((stop.pick, walked))
        return out


def depot(layout: Layout) -> Stop:
    return Stop(layout.depot_x, 0.0)


def distance(a: Stop | Pick, b: Stop | Pick, aisle_length: float) -> float:
    """Shortest walk between two points that are in an aisle or on the front cross aisle.

    In the same aisle the picker walks straight. Otherwise they leave through the front or the back
    cross aisle, whichever is shorter.
    """
    if math.isclose(a.x, b.x):
        return abs(a.y - b.y)
    front = a.y + b.y
    back = 2 * aisle_length - a.y - b.y
    return min(front, back) + abs(a.x - b.x)


def path(a: Stop, b: Stop, aisle_length: float) -> list[Stop]:
    """The stops after ``a`` on a shortest walk to ``b`` (``b`` included)."""
    if math.isclose(a.x, b.x):
        return [b]
    cross = 0.0 if a.y + b.y <= 2 * aisle_length - a.y - b.y else aisle_length
    out = [Stop(a.x, cross), Stop(b.x, cross), b]
    return out[1:] if _same_point(out[0], a) else out


def route_from_sequence(strategy: str, layout: Layout, picks: list[Pick]) -> Route:
    """Walk from the depot to each pick in the given order and back."""
    start = depot(layout)
    stops = [start]
    for pick in picks:
        stops.extend(path(stops[-1], Stop(pick.x, pick.y, pick), layout.aisle_length))
    stops.extend(path(stops[-1], start, layout.aisle_length))
    return Route(strategy, stops)


def is_walkable(route: Route, layout: Layout) -> bool:
    """True if every leg runs along an aisle or along a cross aisle (no walking through racks)."""
    aisle_xs = [layout.aisle_x(a) for a in range(1, layout.aisles + 1)]
    cross_ys = (0.0, layout.aisle_length)
    for a, b in zip(route.stops, route.stops[1:], strict=False):
        if _same_point(a, b):
            continue
        if math.isclose(a.x, b.x):
            if not any(math.isclose(a.x, x) for x in aisle_xs):
                return False
        elif math.isclose(a.y, b.y):
            if not any(math.isclose(a.y, y) for y in cross_ys):
                return False
        else:
            return False
    return True


def _same_point(a: Stop, b: Stop) -> bool:
    return math.isclose(a.x, b.x) and math.isclose(a.y, b.y)
