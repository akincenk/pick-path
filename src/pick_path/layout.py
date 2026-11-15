"""Warehouse geometry: parallel aisles joined by a front and a back cross aisle."""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, fields
from pathlib import Path

# Matches A03-12, 3-12 and A03-12-L. The side (L or R) is accepted but does not change the distance.
DEFAULT_PATTERN = r"A?(?P<aisle>\d+)-(?P<bay>\d+)(?:-(?P<side>[LR]))?"


class LayoutError(ValueError):
    """The layout file or a location code is not valid."""


@dataclass(frozen=True)
class Layout:
    """A single-block warehouse.

    Aisles run front to back and are numbered from 1, left to right. Aisle 1 is at x = 0 and the
    next one ``aisle_spacing`` metres to the right. Bays are numbered from 1 at the front. The front
    cross aisle is at y = 0 and the back cross aisle at y = ``aisle_length``. The depot, where every
    route starts and ends, sits on the front cross aisle at x = ``depot_x``.
    """

    aisles: int
    bays_per_aisle: int
    bay_length: float = 1.0
    aisle_spacing: float = 3.0
    depot_x: float = 0.0
    location_pattern: str = DEFAULT_PATTERN

    def __post_init__(self) -> None:
        if self.aisles < 1 or self.bays_per_aisle < 1:
            raise LayoutError("aisles and bays_per_aisle must be at least 1")
        if self.bay_length <= 0 or self.aisle_spacing <= 0:
            raise LayoutError("bay_length and aisle_spacing must be greater than 0")
        if not 0 <= self.depot_x <= self.aisle_x(self.aisles):
            raise LayoutError(f"depot_x must be between 0 and {self.aisle_x(self.aisles)} (the last aisle)")
        try:
            compiled = re.compile(self.location_pattern)
        except re.error as exc:
            raise LayoutError(f"location_pattern is not a valid regular expression: {exc}") from exc
        if not {"aisle", "bay"} <= set(compiled.groupindex):
            raise LayoutError("location_pattern needs named groups 'aisle' and 'bay'")

    @property
    def aisle_length(self) -> float:
        return self.bays_per_aisle * self.bay_length

    def aisle_x(self, aisle: int) -> float:
        return (aisle - 1) * self.aisle_spacing

    def bay_y(self, bay: int) -> float:
        """Distance from the front cross aisle to the middle of a bay."""
        return (bay - 0.5) * self.bay_length

    def parse(self, code: str) -> tuple[int, int]:
        """Return (aisle, bay) for a location code, or raise LayoutError."""
        match = re.fullmatch(self.location_pattern, code.strip())
        if match is None:
            raise LayoutError(f"location {code!r} does not match the location pattern")
        aisle, bay = int(match["aisle"]), int(match["bay"])
        if not 1 <= aisle <= self.aisles:
            raise LayoutError(f"location {code!r}: aisle {aisle} is outside 1-{self.aisles}")
        if not 1 <= bay <= self.bays_per_aisle:
            raise LayoutError(f"location {code!r}: bay {bay} is outside 1-{self.bays_per_aisle}")
        return aisle, bay


_INT_FIELDS = {"aisles", "bays_per_aisle"}
_FLOAT_FIELDS = {"bay_length", "aisle_spacing", "depot_x"}


def load_layout(path: str | Path) -> Layout:
    """Read a layout from a TOML file with the same keys as :class:`Layout`."""
    try:
        with open(path, "rb") as fh:
            data = tomllib.load(fh)
    except tomllib.TOMLDecodeError as exc:
        raise LayoutError(f"{path}: {exc}") from exc
    known = {f.name for f in fields(Layout)}
    unknown = sorted(set(data) - known)
    if unknown:
        raise LayoutError(f"{path}: unknown keys {', '.join(unknown)}")
    for key, value in data.items():
        if key in _INT_FIELDS and (isinstance(value, bool) or not isinstance(value, int)):
            raise LayoutError(f"{path}: {key} must be a whole number")
        if key in _FLOAT_FIELDS and (isinstance(value, bool) or not isinstance(value, int | float)):
            raise LayoutError(f"{path}: {key} must be a number")
        if key == "location_pattern" and not isinstance(value, str):
            raise LayoutError(f"{path}: location_pattern must be a string")
    try:
        return Layout(**data)
    except TypeError as exc:  # missing required keys
        raise LayoutError(f"{path}: {exc}") from exc
