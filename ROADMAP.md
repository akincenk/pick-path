# Roadmap

Planned work after the first version, roughly in order. Estimates are for one person and include tests and docs. Each item has a GitHub issue. Total: about 31 hours.

## 1. Optimal routes for any list size (6 h)

`exact` stops at 12 locations. For a single-block warehouse there is a polynomial-time optimal method (Ratliff and Rosenthal, 1983) that walks the aisles left to right and keeps a small table of connectivity states. Implement it as `optimal`, check it against `exact` on random lists up to 12 locations, and use it as the baseline in `compare` for larger lists.

## 2. Middle cross aisles (5 h)

Many warehouses have one or more cross aisles part way down the racks. Extend `Layout` with `cross_aisles` (positions in bays), update the distance function to use any cross aisle, and add the combined heuristic from Roodbergen and De Koster (2001). Existing single-block layouts must give the same results as before.

## 3. Route map as SVG (3 h)

`pick-path route ... --svg route.svg` draws the racks, the depot, the route line and numbered pick points. Plain SVG, no dependencies. A golden-file test keeps the output stable.

## 4. Order batching (4 h)

Pick several small orders in one trip. Read an `order` column, a cart capacity (orders or units per trip) and build batches with a seed rule and the savings method, then route each batch. Report trips and total metres against picking order by order.

## 5. Time estimate (1.5 h)

Turn metres into minutes: walking speed, a fixed time per pick line and per unit, set in the layout file or on the command line. Show both in `route` and `compare`.

## 6. Separate start and end points (1.5 h)

Pickers often start at the pick-list printer and finish at packing. Add `start_x` and `end_x` (both on the front cross aisle) and make every strategy and the solvers respect them.

## 7. Wide aisles (2 h)

In a wide aisle, picking from both sides means crossing it. Add an optional `aisle_width` and count the side change when consecutive picks in an aisle are on different sides. Location codes already carry the side (`-L`, `-R`).

## 8. Blocked and one-way aisles (2.5 h)

Mark aisles as closed (for example during a replenishment) or one-way (narrow aisles, forklift traffic). Heuristics skip or route round them; the solvers use a distance that respects them. Clear error if a pick cannot be reached.

## 9. JSON output and pipes (1 h)

`--format json` for `route` and `compare`, `-` for stdin and stdout, so the tool can sit behind a pick-list printer script or a small web service.

## 10. Benchmark command (2 h)

`pick-path benchmark --layout L --orders 1000 --lines 5-15 --seed 1` generates random pick lists, optionally weighted towards fast movers near the front, and prints the average distance per strategy with the spread. Useful for deciding whether a routing change is worth it for a given layout.

## 11. Location map for irregular layouts (2.5 h)

Not every site is a neat grid. Allow a CSV that maps each location code to an aisle and a distance from the front, overriding the pattern and bay length. Validate that every mapped aisle exists and that positions are inside it.
