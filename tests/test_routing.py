import pytest

from pick_path import Stop, distance, is_walkable, make_pick
from pick_path.routing import Route, path, route_from_sequence


def test_distance_same_aisle():
    assert distance(Stop(3, 2), Stop(3, 8), 10) == 6


def test_distance_uses_shorter_cross_aisle():
    # front: 2 + 3 = 5, back: 8 + 7 = 15, plus 6 across
    assert distance(Stop(0, 2), Stop(6, 3), 10) == 11
    # front: 9 + 8 = 17, back: 1 + 2 = 3, plus 3 across
    assert distance(Stop(0, 9), Stop(3, 8), 10) == 6


def test_distance_is_symmetric():
    a, b = Stop(0, 7.5), Stop(9, 1.5)
    assert distance(a, b, 12) == distance(b, a, 12)


def test_path_goes_round_the_rack():
    assert path(Stop(0, 9), Stop(3, 8), 10) == [Stop(0, 10), Stop(3, 10), Stop(3, 8)]
    assert path(Stop(0, 0), Stop(3, 4), 10) == [Stop(3, 0), Stop(3, 4)]


def test_route_from_sequence_matches_distance(small):
    picks = [make_pick(small, c) for c in ["A01-09", "A02-08", "A03-01"]]
    route = route_from_sequence("manual", small, picks)
    legs = [Stop(0, 0), *picks, Stop(0, 0)]
    expected = sum(distance(a, b, 10) for a, b in zip(legs, legs[1:], strict=False))
    assert route.distance == pytest.approx(expected)
    assert is_walkable(route, small)
    # 8.5 up aisle 1; out the back to A02-08 (1.5 + 3 + 2.5); out the front to A03-01 (7.5 + 3 + 0.5)
    assert [w for _, w in route.visits()] == pytest.approx([8.5, 15.5, 26.5])


def test_is_walkable_rejects_shortcuts(small):
    assert not is_walkable(Route("bad", [Stop(0, 0), Stop(3, 5)]), small)  # diagonal
    assert not is_walkable(Route("bad", [Stop(0, 5), Stop(3, 5)]), small)  # through a rack
    assert not is_walkable(Route("bad", [Stop(1.5, 0), Stop(1.5, 5)]), small)  # up a rack, not an aisle
