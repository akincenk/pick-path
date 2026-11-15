"""Reading a pick list from CSV."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

from .layout import Layout, LayoutError

MAX_ERRORS_SHOWN = 10


class PickListError(ValueError):
    """The pick list cannot be used. ``errors`` holds one message per bad line."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        shown = errors[:MAX_ERRORS_SHOWN]
        more = len(errors) - len(shown)
        text = "\n".join(shown) + (f"\n... and {more} more" if more else "")
        super().__init__(text)


@dataclass(frozen=True)
class Pick:
    """One line of the pick list, placed in the warehouse."""

    location: str
    aisle: int
    bay: int
    x: float
    y: float
    line: int = 0
    row: dict[str, str] = field(default_factory=dict, compare=False)


def make_pick(layout: Layout, location: str, line: int = 0, row: dict[str, str] | None = None) -> Pick:
    aisle, bay = layout.parse(location)
    return Pick(location.strip(), aisle, bay, layout.aisle_x(aisle), layout.bay_y(bay), line, row or {})


def load_picks(path: str | Path, layout: Layout, column: str = "location") -> list[Pick]:
    """Read picks from a CSV file with a header row. Every bad line is reported, not just the first."""
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            raise PickListError([f"{path}: file is empty"])
        if column not in reader.fieldnames:
            raise PickListError([f"{path}: no column named {column!r} (found: {', '.join(reader.fieldnames)})"])
        picks: list[Pick] = []
        errors: list[str] = []
        for row in reader:
            line = reader.line_num
            location = (row.get(column) or "").strip()
            if not location:
                errors.append(f"line {line}: empty {column}")
                continue
            try:
                picks.append(make_pick(layout, location, line, {k: v or "" for k, v in row.items() if k}))
            except LayoutError as exc:
                errors.append(f"line {line}: {exc}")
    if errors:
        raise PickListError(errors)
    if not picks:
        raise PickListError([f"{path}: no picks"])
    return picks
