from pathlib import Path

import pytest

from pick_path import Layout

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


@pytest.fixture
def small() -> Layout:
    # 3 aisles, 10 bays of 1 m, aisles 3 m apart: aisle x = 0, 3, 6; aisle length 10 m.
    return Layout(aisles=3, bays_per_aisle=10, bay_length=1.0, aisle_spacing=3.0)


@pytest.fixture
def examples() -> Path:
    return EXAMPLES
