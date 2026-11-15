"""Command line: pick-path route | compare | strategies."""

from __future__ import annotations

import argparse
import csv
import sys

from . import STRATEGIES
from .layout import LayoutError, load_layout
from .picks import PickListError, load_picks
from .routing import Route, RouteError

DESCRIPTIONS = {
    "s-shape": "walk through every aisle with a pick",
    "return": "enter and leave every aisle from the front",
    "midpoint": "front half from the front, back half from the back",
    "largest-gap": "skip the largest empty stretch of each aisle",
    "nearest": "always go to the closest unvisited location",
    "two-opt": "nearest, then improved by 2-opt swaps",
    "exact": "shortest possible route (up to 12 locations)",
}


def _load(args: argparse.Namespace):
    layout = load_layout(args.layout)
    return layout, load_picks(args.picks, layout, args.column)


def _write_route(route: Route, out) -> None:
    visits = route.visits()
    extra = [k for k in visits[0][0].row if k != "location"] if visits else []
    writer = csv.writer(out)
    writer.writerow(["step", "location", "walked_m", *extra])
    for step, (pick, walked) in enumerate(visits, 1):
        writer.writerow([step, pick.location, f"{walked:.1f}", *(pick.row.get(k, "") for k in extra)])


def _print_route(route: Route) -> None:
    visits = route.visits()
    extra = [k for k in visits[0][0].row if k != "location"]
    header = ["#", "location", "walked m", *extra]
    rows = [[str(i), p.location, f"{w:.1f}", *(p.row.get(k, "") for k in extra)] for i, (p, w) in enumerate(visits, 1)]
    widths = [max(len(r[c]) for r in [header, *rows]) for c in range(len(header))]
    for r in [header, *rows]:
        print("  ".join(cell.ljust(w) for cell, w in zip(r, widths, strict=True)).rstrip())
    print(f"\n{route.strategy}: {route.distance:.1f} m for {len(visits)} picks, back at the depot")


def cmd_route(args: argparse.Namespace) -> int:
    layout, picks = _load(args)
    route = STRATEGIES[args.strategy](layout, picks)
    if args.output:
        with open(args.output, "w", newline="", encoding="utf-8") as fh:
            _write_route(route, fh)
        print(f"{route.strategy}: {route.distance:.1f} m for {len(route.picks)} picks, written to {args.output}")
    else:
        _print_route(route)
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    layout, picks = _load(args)
    results: list[tuple[str, float | None, str]] = []
    for name, strategy in STRATEGIES.items():
        try:
            results.append((name, strategy(layout, picks).distance, ""))
        except RouteError as exc:
            results.append((name, None, str(exc)))
    best = min(d for _, d, _ in results if d is not None)
    print(f"{len(picks)} picks\n")
    print(f"{'strategy':<12}  {'metres':>8}  {'vs best':>7}")
    for name, dist, note in results:
        if dist is None:
            print(f"{name:<12}  {'-':>8}  {'':>7}  skipped: {note}")
        else:
            extra = f"+{(dist / best - 1) * 100:.0f}%" if dist > best + 1e-9 else "best"
            print(f"{name:<12}  {dist:>8.1f}  {extra:>7}")
    return 0


def cmd_strategies(args: argparse.Namespace) -> int:
    for name in STRATEGIES:
        print(f"{name:<12}  {DESCRIPTIONS[name]}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pick-path", description="Order picking routes for a warehouse.")
    sub = parser.add_subparsers(dest="command", required=True)

    def with_inputs(p: argparse.ArgumentParser) -> None:
        p.add_argument("picks", help="CSV pick list with a header row")
        p.add_argument("--layout", required=True, help="warehouse layout TOML file")
        p.add_argument("--column", default="location", help="CSV column with the location code")

    route = sub.add_parser("route", help="print the picking route for one strategy")
    with_inputs(route)
    route.add_argument("--strategy", choices=list(STRATEGIES), default="largest-gap")
    route.add_argument("-o", "--output", help="write the route as CSV instead of printing it")
    route.set_defaults(func=cmd_route)

    compare = sub.add_parser("compare", help="walking distance of every strategy for one pick list")
    with_inputs(compare)
    compare.set_defaults(func=cmd_compare)

    strategies = sub.add_parser("strategies", help="list the routing strategies")
    strategies.set_defaults(func=cmd_strategies)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (LayoutError, PickListError, RouteError, OSError) as exc:
        print(f"pick-path: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
