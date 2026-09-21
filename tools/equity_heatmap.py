#!/usr/bin/env python3
"""Render the pre-flop equity table as a heat map.

The table is 169 starting hands x 9 opponent counts, which is hard to judge as
JSON and obvious as a picture: a correct table fades smoothly from AA in the
top-left corner to 32o in the bottom-right, and sampling noise shows up as cells
breaking that gradient.

Laid out the way poker range charts always are - rows and columns running A to 2,
suited above the diagonal, offsuit below it, pairs down the middle.

    python -m tools.equity_heatmap                     # heads-up, in the terminal
    python -m tools.equity_heatmap --opponents 5
    python -m tools.equity_heatmap --view suited       # the suited-vs-offsuit gap
    python -m tools.equity_heatmap --checks            # quality checks only
    python -m tools.equity_heatmap --html grid.html    # standalone page
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from poker.config import PREFLOP_TABLE_PATH
from poker.console import enable_utf8_output
from poker.notation import NOTATION_RANKS

TEMPLATE = Path(__file__).resolve().parent / "templates" / "equity_heatmap.html"
DATA_PLACEHOLDER = "/* __EQUITY_DATA__ */ null"

# Sequential blue, light -> dark. One hue: magnitude is the only thing encoded.
SEQUENTIAL = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7",
              "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281",
              "#0d366b"]
# Diverging: two opposed hues through a neutral grey, for signed values.
DIVERGING_POSITIVE = "#2a78d6"
DIVERGING_NEGATIVE = "#e34948"
DIVERGING_MIDPOINT = "#8a8a86"

EQUITY_FIELD = 3
WIN_FIELD = 0


# --------------------------------------------------------------------------
# data
# --------------------------------------------------------------------------

def load_table(path=None) -> dict:
    """Read the built table, or explain how to build it."""
    path = Path(path or PREFLOP_TABLE_PATH)
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        raise SystemExit(
            f"No equity table at {path}.\n"
            "Build it first: python -m tools.build_equity_table --simulations 10000"
        )


def hand_at(row: int, column: int, ranks: Sequence[str] = NOTATION_RANKS) -> str:
    """The hand a grid position holds.

    Above the diagonal is suited, below it offsuit, and the diagonal is pairs -
    the layout every poker range chart uses.
    """
    if row == column:
        return ranks[row] * 2
    high, low = ranks[min(row, column)], ranks[max(row, column)]
    return f"{high}{low}" + ("s" if row < column else "o")


def equity_of(table: dict, hand: str, opponents: int) -> float:
    return table["table"][hand][str(opponents)][EQUITY_FIELD]


def equity_grid(table: dict, opponents: int) -> List[List[float]]:
    ranks = NOTATION_RANKS
    return [[equity_of(table, hand_at(r, c, ranks), opponents)
             for c in range(len(ranks))] for r in range(len(ranks))]


def suited_edge_grid(table: dict, opponents: int) -> List[List[Optional[float]]]:
    """Suited minus offsuit for the same two ranks; None on the diagonal.

    The strictest check on the table: the gap averages under 3 points while the
    sampling error is around half a point, so getting its sign right in all 78
    pairs says more than any single hand matching a published figure.
    """
    ranks = NOTATION_RANKS
    grid: List[List[Optional[float]]] = []
    for r in range(len(ranks)):
        row: List[Optional[float]] = []
        for c in range(len(ranks)):
            if r == c:
                row.append(None)
            else:
                high, low = ranks[min(r, c)], ranks[max(r, c)]
                row.append(equity_of(table, f"{high}{low}s", opponents)
                           - equity_of(table, f"{high}{low}o", opponents))
        grid.append(row)
    return grid


# --------------------------------------------------------------------------
# colour
# --------------------------------------------------------------------------

def _rgb(hex_colour: str) -> Tuple[int, int, int]:
    h = hex_colour.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _mix(first: str, second: str, t: float) -> Tuple[int, int, int]:
    a, b = _rgb(first), _rgb(second)
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def sequential_colour(t: float) -> Tuple[int, int, int]:
    """Position on the one-hue ramp, 0 palest to 1 deepest."""
    t = min(1.0, max(0.0, t))
    position = t * (len(SEQUENTIAL) - 1)
    index = min(int(position), len(SEQUENTIAL) - 2)
    return _mix(SEQUENTIAL[index], SEQUENTIAL[index + 1], position - index)


def diverging_colour(t: float) -> Tuple[int, int, int]:
    """Signed position, -1 to 1, through a neutral midpoint at 0."""
    t = min(1.0, max(-1.0, t))
    pole = DIVERGING_POSITIVE if t >= 0 else DIVERGING_NEGATIVE
    return _mix(DIVERGING_MIDPOINT, pole, abs(t))


def _ink(depth: float) -> Tuple[int, int, int]:
    """Label colour that survives its own cell."""
    return (255, 255, 255) if depth > 0.58 else (11, 11, 11)


def _paint(text: str, background: Tuple[int, int, int],
           foreground: Tuple[int, int, int]) -> str:
    return (f"\x1b[48;2;{background[0]};{background[1]};{background[2]}m"
            f"\x1b[38;2;{foreground[0]};{foreground[1]};{foreground[2]}m"
            f"{text}\x1b[0m")


def supports_colour(stream=None) -> bool:
    """Whether to emit ANSI colour at all."""
    stream = stream or sys.stdout
    if os.environ.get("NO_COLOR"):
        return False
    if not hasattr(stream, "isatty") or not stream.isatty():
        return False
    if os.name == "nt":
        # Windows 10+ needs virtual terminal processing turned on, which this
        # call does as a side effect.
        os.system("")
    return True


# --------------------------------------------------------------------------
# terminal rendering
# --------------------------------------------------------------------------

def render_terminal(table: dict, opponents: int, view: str = "equity",
                    colour: bool = True) -> str:
    ranks = NOTATION_RANKS
    if view == "suited":
        grid = suited_edge_grid(table, opponents)
        values = [v for row in grid for v in row if v is not None]
        extent = max(abs(min(values)), abs(max(values))) or 1.0
    else:
        grid = equity_grid(table, opponents)
        values = [v for row in grid for v in row]
        low, high = min(values), max(values)
        span = (high - low) or 1.0

    lines = []
    lines.append("     " + "".join(f"{rank:>5}" for rank in ranks))

    for r, rank in enumerate(ranks):
        cells = []
        for c in range(len(ranks)):
            value = grid[r][c]
            if value is None:
                cells.append("     ")
                continue
            if view == "suited":
                depth = abs(value) / extent
                background = diverging_colour(value / extent)
                label = f"{value * 100:+4.1f} "
            else:
                depth = (value - low) / span
                background = sequential_colour(depth)
                label = f"{value * 100:4.1f} "
            cells.append(_paint(label, background, _ink(depth)) if colour else label)
        lines.append(f"{rank:>3}  " + "".join(cells))

    lines.append("")
    if view == "suited":
        lines.append(f"  suited minus offsuit, in points of equity "
                     f"(range {min(values) * 100:+.1f} to {max(values) * 100:+.1f})")
        lines.append("  above the diagonal mirrors below it; the diagonal has no suited form")
    else:
        lines.append(f"  equity vs {opponents} opponent{'s' if opponents != 1 else ''}, "
                     f"in percent (range {low * 100:.1f} to {high * 100:.1f})")
        lines.append("  suited above the diagonal, offsuit below, pairs on it")
    return "\n".join(lines)


def render_scale(colour: bool = True, width: int = 40) -> str:
    """A ramp legend, so the colours name values rather than a vibe."""
    if not colour:
        return ""
    blocks = "".join(
        _paint(" ", sequential_colour(i / (width - 1)), (0, 0, 0))
        for i in range(width)
    )
    return f"  low {blocks} high"


# --------------------------------------------------------------------------
# quality checks
# --------------------------------------------------------------------------

PUBLISHED = {"AA": 0.852, "KK": 0.824, "QQ": 0.799, "JJ": 0.775, "TT": 0.751,
             "AKs": 0.670, "AKo": 0.653, "AQs": 0.663, "72o": 0.354, "32o": 0.323}


def quality_checks(table: dict) -> List[Tuple[str, str, bool]]:
    """Checks a correct table must pass, as (name, value, passed)."""
    hands = table["table"]
    cells = sum(len(row) for row in hands.values())

    def rises_with_opponents(row: dict) -> bool:
        """True if equity ever goes up as the table gets bigger.

        Missing cells are the business of the count check above, so skip rather
        than raise on them - a partial table should be reported, not crash the
        report.
        """
        for n in range(1, 9):
            here, nxt = row.get(str(n)), row.get(str(n + 1))
            if here is None or nxt is None:
                continue
            if here[EQUITY_FIELD] < nxt[EQUITY_FIELD] - 0.01:
                return True
        return False

    not_monotonic = [hand for hand, row in hands.items() if rises_with_opponents(row)]

    edges = []
    for i, high in enumerate(NOTATION_RANKS):
        for low in NOTATION_RANKS[i + 1:]:
            edges.append(equity_of(table, f"{high}{low}s", 1)
                         - equity_of(table, f"{high}{low}o", 1))
    wrong_sign = [e for e in edges if e <= 0]

    worst_hand, worst_gap = max(
        ((hand, equity_of(table, hand, 1) - expected)
         for hand, expected in PUBLISHED.items()),
        key=lambda pair: abs(pair[1]),
    )

    return [
        ("cells present", f"{cells} / 1521", cells == 1521),
        ("equity falls as opponents are added",
         f"{len(hands) - len(not_monotonic)} / {len(hands)} hands",
         not not_monotonic),
        ("suited beats offsuit",
         f"{len(edges) - len(wrong_sign)} / {len(edges)} pairs", not wrong_sign),
        ("smallest suited edge", f"{min(edges) * 100:+.2f} pp", min(edges) > 0),
        ("mean suited edge", f"{sum(edges) / len(edges) * 100:+.2f} pp", True),
        ("largest gap vs published",
         f"{worst_hand} {worst_gap * 100:+.2f} pp", abs(worst_gap) < 0.02),
    ]


def render_checks(table: dict) -> str:
    lines = [f"  {'check':<38} {'value':>18}"]
    for name, value, ok in quality_checks(table):
        mark = "pass" if ok else "FAIL"
        lines.append(f"  {name:<38} {value:>18}  {mark}")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# html
# --------------------------------------------------------------------------

def build_html(table: dict, template_path=None) -> str:
    """One self-contained page, data inlined."""
    template = Path(template_path or TEMPLATE).read_text(encoding="utf-8")
    if DATA_PLACEHOLDER not in template:
        raise ValueError(f"template has no data placeholder: {template_path or TEMPLATE}")

    checks = quality_checks(table)
    worst = next(value for name, value, _ in checks if name == "largest gap vs published")
    payload = {
        "simulations": table["simulations"],
        "ranks": NOTATION_RANKS,
        "data": {
            hand: [[round(row[str(n)][WIN_FIELD], 4),
                    round(row[str(n)][1], 4),
                    round(row[str(n)][EQUITY_FIELD], 4)] for n in range(1, 10)]
            for hand, row in table["table"].items()
        },
        "published": PUBLISHED,
        "footer": (
            f"Rendered from poker/data/preflop_equity.json by "
            f"tools/equity_heatmap.py. {table['simulations']:,} simulations per "
            f"cell puts the standard error near "
            f"{0.5 / table['simulations'] ** 0.5:.4f}, so single cells can sit a "
            f"point or so off a published figure without anything being wrong - "
            f"the largest here is {worst}."
        ),
    }
    return template.replace(DATA_PLACEHOLDER,
                            json.dumps(payload, separators=(",", ":")))


# --------------------------------------------------------------------------
# cli
# --------------------------------------------------------------------------

def main(argv=None) -> int:
    enable_utf8_output()
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--opponents", type=int, default=1, choices=range(1, 10),
                        metavar="1-9", help="table size to show (default: 1)")
    parser.add_argument("--view", choices=("equity", "suited"), default="equity",
                        help="equity, or the suited-versus-offsuit gap")
    parser.add_argument("--html", metavar="PATH",
                        help="write a standalone interactive page instead")
    parser.add_argument("--checks", action="store_true",
                        help="print the quality checks only")
    parser.add_argument("--no-color", action="store_true",
                        help="plain numbers, no ANSI colour")
    parser.add_argument("--table", metavar="PATH",
                        help="read a table from somewhere other than the default")
    args = parser.parse_args(argv)

    table = load_table(args.table)

    if args.html:
        destination = Path(args.html)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(build_html(table), encoding="utf-8")
        size = destination.stat().st_size / 1024
        print(f"Wrote {destination} ({size:.0f} KB) - open it in a browser.")
        return 0

    if args.checks:
        print(render_checks(table))
        return 0

    colour = not args.no_color and supports_colour()
    print()
    print(render_terminal(table, args.opponents, args.view, colour))
    if args.view == "equity" and colour:
        print()
        print(render_scale(colour))
    print()
    print(render_checks(table))
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
