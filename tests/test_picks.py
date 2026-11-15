import pytest

from pick_path import PickListError, load_picks


def test_load_example(examples, small):
    from pick_path import load_layout

    layout = load_layout(examples / "layout.toml")
    picks = load_picks(examples / "picks.csv", layout)
    assert len(picks) == 8
    first = picks[0]
    assert (first.location, first.aisle, first.bay, first.line) == ("A02-04", 2, 4, 2)
    assert first.row["sku"] == "WIDGET-0042"


def test_reports_every_bad_line(tmp_path, small):
    path = tmp_path / "p.csv"
    path.write_text("location,sku\nA01-01,X\nA09-01,Y\n,Z\nnonsense,W\n")
    with pytest.raises(PickListError) as info:
        load_picks(path, small)
    assert [e.split(":")[0] for e in info.value.errors] == ["line 3", "line 4", "line 5"]


def test_missing_column(tmp_path, small):
    path = tmp_path / "p.csv"
    path.write_text("bin,sku\nA01-01,X\n")
    with pytest.raises(PickListError, match="no column named 'location'"):
        load_picks(path, small)


@pytest.mark.parametrize("text", ["", "location,sku\n"])
def test_empty(tmp_path, small, text):
    path = tmp_path / "p.csv"
    path.write_text(text)
    with pytest.raises(PickListError):
        load_picks(path, small)


def test_other_column_and_bom(tmp_path, small):
    path = tmp_path / "p.csv"
    path.write_bytes("﻿bin\nA03-10\n".encode())
    assert load_picks(path, small, column="bin")[0].aisle == 3
