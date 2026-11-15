import itertools
import random

import pytest

from pick_path import STRATEGIES, Layout, RouteError, is_walkable, make_pick
from pick_path.routing import route_from_sequence
from pick_path.tsp import exact, nearest_neighbour, two_opt


def picks_of(layout, codes):
    return [make_pick(layout, c, line=i) for i, c in enumerate(codes)]


def random_picks(layout, rng, n):
    codes = [f"A{rng.randint(1, layout.aisles):02}-{rng.randint(1, layout.bays_per_aisle):02}" for _ in range(n)]
    return picks_of(layout, codes)


def brute_force(layout, picks):
    return min(route_from_sequence("bf", layout, list(p)).distance for p in itertools.permutations(picks))


def test_hand_computed(small):
    picks = picks_of(small, ["A01-02", "A02-05", "A03-09"])
    # up aisle 1 (10), across the back (3), down aisle 2 (10), along the front (3),
    # in and out of aisle 3 to 8.5 m (17), home (6)
    assert STRATEGIES["s-shape"](small, picks).distance == 49
    # 1.5*2 + 3 + 4.5*2 + 3 + 8.5*2 + 6
    assert STRATEGIES["return"](small, picks).distance == 41
    assert exact(small, picks).distance == pytest.approx(brute_force(small, picks))


def test_largest_gap_takes_items_from_the_near_end(small):
    picks = picks_of(small, ["A01-05", "A02-01", "A02-10", "A03-05"])
    route = STRATEGIES["largest-gap"](small, picks)
    # aisle 2: bay 10 from the back on the way out, bay 1 from the front on the way home
    assert [p.location for p in route.picks] == ["A01-05", "A02-10", "A03-05", "A02-01"]
    assert route.distance == 10 + 3 + 1 + 3 + 10 + 3 + 1 + 3


@pytest.mark.parametrize("name", list(STRATEGIES))
@pytest.mark.parametrize("seed", range(25))
def test_every_route_is_walkable_and_complete(name, seed):
    rng = random.Random(seed)
    layout = Layout(
        aisles=rng.randint(1, 9),
        bays_per_aisle=rng.randint(1, 30),
        bay_length=rng.choice([0.9, 1.0, 1.2]),
        aisle_spacing=rng.choice([2.5, 3.0, 4.0]),
    )
    layout = Layout(**{**layout.__dict__, "depot_x": rng.uniform(0, layout.aisle_x(layout.aisles))})
    picks = random_picks(layout, rng, rng.randint(1, 10))
    route = STRATEGIES[name](layout, picks)
    assert is_walkable(route, layout)
    assert sorted(p.line for p in route.picks) == sorted(p.line for p in picks)
    assert route.stops[0] == route.stops[-1]
    assert route.distance >= exact(layout, picks).distance - 1e-9


@pytest.mark.parametrize("seed", range(15))
def test_exact_matches_brute_force(seed, small):
    rng = random.Random(seed)
    picks = random_picks(small, rng, rng.randint(1, 6))
    assert exact(small, picks).distance == pytest.approx(brute_force(small, picks))


@pytest.mark.parametrize("seed", range(15))
def test_two_opt_never_worse_than_nearest(seed):
    rng = random.Random(seed)
    layout = Layout(aisles=10, bays_per_aisle=25)
    picks = random_picks(layout, rng, 30)
    assert two_opt(layout, picks).distance <= nearest_neighbour(layout, picks).distance + 1e-9


def test_exact_refuses_large_lists():
    layout = Layout(aisles=10, bays_per_aisle=25)
    picks = picks_of(layout, [f"A{a:02}-{b:02}" for a in range(1, 11) for b in (1, 20)])
    with pytest.raises(RouteError, match="12 or fewer"):
        exact(layout, picks)


def test_same_location_twice_costs_nothing_extra(small):
    once = exact(small, picks_of(small, ["A02-05"]))
    twice = exact(small, picks_of(small, ["A02-05", "A02-05"]))
    assert once.distance == twice.distance and len(twice.picks) == 2


def test_depot_on_the_right_starts_from_the_right():
    layout = Layout(aisles=3, bays_per_aisle=10, aisle_spacing=3.0, depot_x=6.0)
    route = STRATEGIES["s-shape"](layout, picks_of(layout, ["A01-02", "A03-02"]))
    assert [p.location for p in route.picks] == ["A03-02", "A01-02"]
