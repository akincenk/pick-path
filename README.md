# pick-path

Plan the walk for an order picker in a warehouse with parallel aisles. Give it a layout and a pick list, and it puts the picks in walking order and tells you how many metres the route is. It can also compare the common routing methods on the same list, so you can see what a better route would save before changing how people pick.

## Who it is for

Small and mid-size warehouses and stockrooms that pick from shelving or racking in parallel aisles, often from a printed pick list. Picking is usually the most labour-heavy job in a warehouse and most of that time is walking. Many sites print pick lists in SKU or order-line order, which sends pickers back and forth. Sorting the list into a sensible route is a cheap fix, and this tool shows how much it is worth for your own layout and orders.

## What it does

- Reads a layout (number of aisles, bays per aisle, bay length, aisle spacing, depot position) from a small TOML file.
- Reads a pick list from CSV. Location codes like `A03-12` (aisle 3, bay 12) by default; the format is a regular expression in the layout file. Every bad line is reported with its line number.
- Builds a route with one of seven strategies and prints it in walking order with the distance walked so far, or writes it as CSV.
- Compares all strategies on one pick list.

| Strategy | Rule |
| --- | --- |
| `s-shape` | walk through every aisle that has a pick |
| `return` | go into each aisle from the front and come back out |
| `midpoint` | front half of each aisle from the front, back half from the back |
| `largest-gap` | in each aisle, skip the longest stretch with nothing to pick |
| `nearest` | always walk to the closest location not yet visited |
| `two-opt` | `nearest`, then improved by reversing parts of the route while it gets shorter |
| `exact` | the shortest possible route (Held-Karp), for up to 12 distinct locations |

The first four are rules a picker can follow on paper. The last three are computed orders that a handheld or a sorted pick list would give them.

## Install

Python 3.11 or newer. No runtime dependencies.

```sh
git clone https://github.com/akincenk/pick-path
cd pick-path
python3 -m venv .venv && . .venv/bin/activate
pip install -e .            # add '.[dev]' to run the tests
```

## Use

```sh
pick-path strategies
pick-path route examples/picks.csv --layout examples/layout.toml
pick-path route examples/picks.csv --layout examples/layout.toml --strategy s-shape -o route.csv
pick-path compare examples/picks.csv --layout examples/layout.toml
```

`compare` on the example data:

```text
8 picks

strategy        metres  vs best
s-shape          151.2     +20%
return           216.0     +71%
midpoint         127.2      +1%
largest-gap      127.2      +1%
nearest          132.0      +5%
two-opt          126.0     best
exact            126.0     best
```

The pick list needs a header row and a `location` column (`--column` for another name). Every other column is passed through to the output, so order numbers, SKUs and quantities stay with each line:

```csv
order,location,sku,qty
SO-1001,A02-04,WIDGET-0042,2
SO-1002,A03-15,TAPE-48MM,6
```

### Layout file

```toml
aisles = 8             # numbered 1.. from left to right
bays_per_aisle = 20    # numbered 1.. from the front
bay_length = 1.2       # metres along the aisle per bay
aisle_spacing = 3.0    # metres between aisle centre lines
depot_x = 0.0          # where routes start and end, on the front cross aisle (0 = aisle 1)
# location_pattern = 'A?(?P<aisle>\d+)-(?P<bay>\d+)(?:-(?P<side>[LR]))?'
```

## How it works

The model is the standard single-block warehouse from the order-picking literature:

- Aisles are parallel and joined by a cross aisle at the front and one at the back. The depot is on the front cross aisle.
- A pick location is the middle of its bay on the aisle centre line. Both sides of an aisle are reached from the centre line, so `-L` and `-R` do not change the distance.
- The shortest walk between two locations in different aisles goes round the rack through the front or the back cross aisle, whichever is shorter.

Code layout:

| File | Role |
| --- | --- |
| `src/pick_path/layout.py` | `Layout`, location parsing, TOML loading |
| `src/pick_path/picks.py` | CSV pick list loading with per-line errors |
| `src/pick_path/routing.py` | distance in the aisle network, `Route` and `Stop`, the walkability check |
| `src/pick_path/heuristics.py` | S-shape, return, midpoint, largest gap |
| `src/pick_path/tsp.py` | nearest neighbour, 2-opt, exact (Held-Karp) |
| `src/pick_path/cli.py` | the `pick-path` command |

Every strategy returns a `Route`: a list of stops from the depot back to the depot, including the corners where the picker turns into a cross aisle. The tests check every strategy on random layouts and pick lists for three things: the route only uses aisles and cross aisles, every pick is visited exactly once, and no route is shorter than the exact one. The exact solver itself is checked against brute force.

Use as a library:

```python
from pick_path import STRATEGIES, load_layout, load_picks

layout = load_layout("examples/layout.toml")
picks = load_picks("examples/picks.csv", layout)
route = STRATEGIES["largest-gap"](layout, picks)
print(round(route.distance, 1), [p.location for p in route.picks])
```

## Limits

- One block: no middle cross aisles yet, and every aisle has the same length.
- Distances only. Pick time, cart capacity and congestion are not modelled.
- `exact` is limited to 12 distinct locations because its run time doubles with every extra location.

These are the first items in [ROADMAP.md](ROADMAP.md).

## Development

```sh
pip install -e '.[dev]'
ruff check . && ruff format --check . && pytest -q
```

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT, see [LICENSE](LICENSE).
