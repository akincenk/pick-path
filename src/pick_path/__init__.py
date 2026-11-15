"""Order picking routes for a warehouse with parallel aisles."""

from .heuristics import largest_gap, midpoint, return_route, s_shape
from .layout import Layout, LayoutError, load_layout
from .picks import Pick, PickListError, load_picks, make_pick
from .routing import Route, RouteError, Stop, distance, is_walkable
from .tsp import exact, nearest_neighbour, two_opt

STRATEGIES = {
    "s-shape": s_shape,
    "return": return_route,
    "midpoint": midpoint,
    "largest-gap": largest_gap,
    "nearest": nearest_neighbour,
    "two-opt": two_opt,
    "exact": exact,
}

__all__ = [
    "STRATEGIES",
    "Layout",
    "LayoutError",
    "Pick",
    "PickListError",
    "Route",
    "RouteError",
    "Stop",
    "distance",
    "is_walkable",
    "load_layout",
    "load_picks",
    "make_pick",
]
