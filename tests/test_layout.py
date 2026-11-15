import pytest

from pick_path import Layout, LayoutError, load_layout


def test_geometry(small):
    assert small.aisle_length == 10
    assert small.aisle_x(3) == 6
    assert small.bay_y(1) == 0.5


@pytest.mark.parametrize("code,expected", [("A03-12", (3, 12)), ("3-1", (3, 1)), (" A01-10-L ", (1, 10))])
def test_parse(code, expected):
    assert Layout(aisles=5, bays_per_aisle=20).parse(code) == expected


@pytest.mark.parametrize("code", ["A06-01", "A00-01", "A01-21", "A01-00", "B01-01", "A01", ""])
def test_parse_rejects(code):
    with pytest.raises(LayoutError):
        Layout(aisles=5, bays_per_aisle=20).parse(code)


def test_custom_pattern():
    layout = Layout(aisles=4, bays_per_aisle=9, location_pattern=r"(?P<aisle>\d)(?P<bay>\d)")
    assert layout.parse("27") == (2, 7)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"aisles": 0, "bays_per_aisle": 1},
        {"aisles": 1, "bays_per_aisle": 1, "bay_length": 0},
        {"aisles": 2, "bays_per_aisle": 1, "depot_x": 99},
        {"aisles": 2, "bays_per_aisle": 1, "location_pattern": "("},
        {"aisles": 2, "bays_per_aisle": 1, "location_pattern": r"(?P<aisle>\d+)"},
    ],
)
def test_invalid_layout(kwargs):
    with pytest.raises(LayoutError):
        Layout(**kwargs)


def test_load_example(examples):
    layout = load_layout(examples / "layout.toml")
    assert layout.aisles == 8 and layout.aisle_length == pytest.approx(24.0)


@pytest.mark.parametrize(
    "text,message",
    [
        ("aisles = 2\nbays_per_aisle = 3\ncolour = 'red'\n", "unknown keys colour"),
        ("aisles = 2.5\nbays_per_aisle = 3\n", "whole number"),
        ("aisles = 2\nbays_per_aisle = 3\nbay_length = 'long'\n", "must be a number"),
        ("aisles = 2\n", "bays_per_aisle"),
        ("aisles = \n", "Invalid"),
    ],
)
def test_load_errors(tmp_path, text, message):
    path = tmp_path / "layout.toml"
    path.write_text(text)
    with pytest.raises(LayoutError, match=message):
        load_layout(path)
