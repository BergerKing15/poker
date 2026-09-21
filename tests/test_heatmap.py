"""The equity heat map: grid layout, colour scales, quality checks, exports."""

import json
import tempfile
import unittest
from pathlib import Path

from poker.notation import NOTATION_RANKS, all_preflop_keys
from tools import equity_heatmap as heat


def synthetic_table(simulations=10000, **overrides):
    """A complete, well-formed table with plausible values.

    Built rather than loaded so the checks can be tested against data that is
    deliberately wrong, which the real table never is.
    """
    values = {r: v for v, r in enumerate(reversed(NOTATION_RANKS), start=2)}
    table = {}
    for key in all_preflop_keys():
        high = values[key[0]]
        low = values[key[1]]
        suited = key.endswith("s")
        pair = len(key) == 2
        base = 0.32 + (high + low) / 56.0 * 0.3 + (0.2 if pair else 0.0)
        base += 0.03 if suited else 0.0
        row = {}
        for opponents in range(1, 10):
            equity = max(0.02, base / (1 + 0.55 * (opponents - 1)))
            win = equity - 0.015
            row[str(opponents)] = [round(win, 4), 0.015,
                                   round(1 - win - 0.015, 4), round(equity, 4)]
        table[key] = row
    # Pin the hands the published-comparison check looks at, so well-formed
    # synthetic data can pass it; the rest stay plausible rather than real.
    for hand, expected in heat.PUBLISHED.items():
        row = table[hand]["1"]
        row[heat.EQUITY_FIELD] = expected
        row[heat.WIN_FIELD] = round(expected - 0.015, 4)

    payload = {"simulations": simulations, "fields": [], "table": table}
    payload.update(overrides)
    return payload


class TestGridLayout(unittest.TestCase):
    def test_diagonal_is_pairs(self):
        for i, rank in enumerate(NOTATION_RANKS):
            self.assertEqual(heat.hand_at(i, i), rank + rank)

    def test_above_the_diagonal_is_suited(self):
        self.assertEqual(heat.hand_at(0, 1), "AKs")
        self.assertTrue(heat.hand_at(2, 7).endswith("s"))

    def test_below_the_diagonal_is_offsuit(self):
        self.assertEqual(heat.hand_at(1, 0), "AKo")
        self.assertTrue(heat.hand_at(7, 2).endswith("o"))

    def test_mirrored_positions_are_the_same_ranks(self):
        for i in range(13):
            for j in range(13):
                if i == j:
                    continue
                self.assertEqual(heat.hand_at(i, j)[:2], heat.hand_at(j, i)[:2])

    def test_the_grid_covers_all_169_hands(self):
        seen = {heat.hand_at(i, j) for i in range(13) for j in range(13)}
        self.assertEqual(seen, set(all_preflop_keys()))
        self.assertEqual(len(seen), 169)


class TestGrids(unittest.TestCase):
    def setUp(self):
        self.table = synthetic_table()

    def test_equity_grid_is_13_by_13(self):
        grid = heat.equity_grid(self.table, 1)
        self.assertEqual(len(grid), 13)
        self.assertTrue(all(len(row) == 13 for row in grid))

    def test_equity_grid_matches_the_table(self):
        grid = heat.equity_grid(self.table, 3)
        self.assertAlmostEqual(grid[0][0], heat.equity_of(self.table, "AA", 3))
        self.assertAlmostEqual(grid[0][1], heat.equity_of(self.table, "AKs", 3))

    def test_suited_edge_is_blank_on_the_diagonal(self):
        grid = heat.suited_edge_grid(self.table, 1)
        for i in range(13):
            self.assertIsNone(grid[i][i])

    def test_suited_edge_is_symmetric(self):
        grid = heat.suited_edge_grid(self.table, 1)
        for i in range(13):
            for j in range(13):
                if i != j:
                    self.assertAlmostEqual(grid[i][j], grid[j][i])

    def test_suited_edge_is_positive_in_well_formed_data(self):
        grid = heat.suited_edge_grid(self.table, 1)
        edges = [v for row in grid for v in row if v is not None]
        self.assertTrue(all(e > 0 for e in edges))


class TestColourScales(unittest.TestCase):
    def test_sequential_runs_pale_to_deep(self):
        self.assertEqual(heat.sequential_colour(0.0), heat._rgb(heat.SEQUENTIAL[0]))
        self.assertEqual(heat.sequential_colour(1.0), heat._rgb(heat.SEQUENTIAL[-1]))

    def test_sequential_darkens_monotonically(self):
        brightness = [sum(heat.sequential_colour(i / 20)) for i in range(21)]
        for earlier, later in zip(brightness, brightness[1:]):
            self.assertLessEqual(later, earlier)

    def test_sequential_clamps_out_of_range_input(self):
        self.assertEqual(heat.sequential_colour(-5), heat.sequential_colour(0))
        self.assertEqual(heat.sequential_colour(5), heat.sequential_colour(1))

    def test_diverging_is_neutral_at_zero(self):
        self.assertEqual(heat.diverging_colour(0.0), heat._rgb(heat.DIVERGING_MIDPOINT))

    def test_diverging_poles_are_opposite(self):
        positive = heat.diverging_colour(1.0)
        negative = heat.diverging_colour(-1.0)
        self.assertEqual(positive, heat._rgb(heat.DIVERGING_POSITIVE))
        self.assertEqual(negative, heat._rgb(heat.DIVERGING_NEGATIVE))
        # Warm against cool: the red pole must be redder, the blue pole bluer.
        self.assertGreater(negative[0], positive[0])
        self.assertGreater(positive[2], negative[2])

    def test_label_ink_flips_on_deep_fills(self):
        self.assertEqual(heat._ink(0.95), (255, 255, 255))
        self.assertEqual(heat._ink(0.05), (11, 11, 11))

    def test_colour_is_off_when_not_a_terminal(self):
        class NotATty:
            def isatty(self):
                return False
        self.assertFalse(heat.supports_colour(NotATty()))


class TestQualityChecks(unittest.TestCase):
    def names(self, checks):
        return {name: (value, ok) for name, value, ok in checks}

    def test_well_formed_data_passes_everything(self):
        checks = heat.quality_checks(synthetic_table())
        for name, value, ok in checks:
            with self.subTest(check=name):
                self.assertTrue(ok, f"{name} reported {value}")

    def test_missing_cells_are_caught(self):
        table = synthetic_table()
        del table["table"]["AA"]["9"]
        result = self.names(heat.quality_checks(table))
        self.assertFalse(result["cells present"][1])

    def test_non_monotonic_hand_is_caught(self):
        table = synthetic_table()
        # Equity must not rise as opponents are added.
        table["table"]["AA"]["5"][heat.EQUITY_FIELD] = 0.99
        result = self.names(heat.quality_checks(table))
        self.assertFalse(result["equity falls as opponents are added"][1])

    def test_suited_worse_than_offsuit_is_caught(self):
        table = synthetic_table()
        table["table"]["AKs"]["1"][heat.EQUITY_FIELD] = 0.1
        result = self.names(heat.quality_checks(table))
        self.assertFalse(result["suited beats offsuit"][1])
        self.assertFalse(result["smallest suited edge"][1])

    def test_a_wild_published_gap_is_caught(self):
        table = synthetic_table()
        table["table"]["AA"]["1"][heat.EQUITY_FIELD] = 0.10
        result = self.names(heat.quality_checks(table))
        self.assertFalse(result["largest gap vs published"][1])


class TestRendering(unittest.TestCase):
    def setUp(self):
        self.table = synthetic_table()

    def test_terminal_render_has_a_header_and_13_rows(self):
        text = heat.render_terminal(self.table, 1, colour=False)
        lines = text.splitlines()
        self.assertEqual(lines[0].split(), NOTATION_RANKS)
        body = [l for l in lines[1:14]]
        self.assertEqual([l.split()[0] for l in body], NOTATION_RANKS)

    def test_plain_render_emits_no_escape_codes(self):
        text = heat.render_terminal(self.table, 1, colour=False)
        self.assertNotIn("\x1b", text)

    def test_coloured_render_emits_escape_codes_and_resets_them(self):
        text = heat.render_terminal(self.table, 1, colour=True)
        self.assertIn("\x1b[48;2;", text)
        self.assertEqual(text.count("\x1b[0m"), 169)

    def test_suited_view_leaves_the_diagonal_empty(self):
        text = heat.render_terminal(self.table, 1, view="suited", colour=False)
        self.assertIn("suited minus offsuit", text)
        # Count inside the grid only - the caption quotes a range and so
        # carries signs of its own.
        body = text.splitlines()[1:14]
        signed = sum(line.count("+") + line.count("−") for line in body)
        self.assertEqual(signed, 156)  # 169 cells less the 13 on the diagonal

    def test_every_opponent_count_renders(self):
        for opponents in range(1, 10):
            with self.subTest(opponents=opponents):
                text = heat.render_terminal(self.table, opponents, colour=False)
                self.assertIn(f"vs {opponents} opponent", text)

    def test_checks_render_as_text(self):
        text = heat.render_checks(self.table)
        self.assertIn("cells present", text)
        self.assertIn("pass", text)


class TestHtmlExport(unittest.TestCase):
    def test_export_inlines_the_data_and_leaves_no_placeholder(self):
        html = heat.build_html(synthetic_table())
        self.assertNotIn("__EQUITY_DATA__", html)
        self.assertIn('"AKs"', html)
        self.assertIn("<title>", html)

    def test_export_carries_the_simulation_count(self):
        html = heat.build_html(synthetic_table(simulations=4321))
        self.assertIn("4321", html)
        self.assertIn("4,321 simulations", html)

    def test_export_is_a_standalone_file(self):
        html = heat.build_html(synthetic_table())
        self.assertNotIn("equity_data.js", html)

    def test_a_template_without_the_placeholder_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.html"
            bad.write_text("<title>no placeholder</title>", encoding="utf-8")
            with self.assertRaises(ValueError):
                heat.build_html(synthetic_table(), template_path=bad)


class TestLoading(unittest.TestCase):
    def test_missing_table_explains_how_to_build_it(self):
        with self.assertRaises(SystemExit) as caught:
            heat.load_table("no/such/table.json")
        self.assertIn("build_equity_table", str(caught.exception))

    def test_round_trip_through_disk(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t.json"
            path.write_text(json.dumps(synthetic_table()), encoding="utf-8")
            self.assertEqual(heat.load_table(path)["simulations"], 10000)


class TestAgainstTheShippedTable(unittest.TestCase):
    """The real artifact, if it has been built."""

    def setUp(self):
        from poker.config import PREFLOP_TABLE_PATH
        if not PREFLOP_TABLE_PATH.exists():
            self.skipTest("pre-flop table has not been built")
        self.table = heat.load_table()

    def test_the_shipped_table_passes_every_check(self):
        for name, value, ok in heat.quality_checks(self.table):
            with self.subTest(check=name):
                self.assertTrue(ok, f"{name} reported {value}")

    def test_it_renders_at_every_opponent_count_and_view(self):
        for view in ("equity", "suited"):
            for opponents in (1, 5, 9):
                with self.subTest(view=view, opponents=opponents):
                    text = heat.render_terminal(self.table, opponents, view, colour=False)
                    self.assertEqual(len(text.splitlines()), 17)

    def test_aces_are_the_strongest_cell_in_the_grid(self):
        grid = heat.equity_grid(self.table, 1)
        best = max((v, r, c) for r, row in enumerate(grid) for c, v in enumerate(row))
        self.assertEqual(heat.hand_at(best[1], best[2]), "AA")

    def test_the_suited_edge_grows_as_the_cards_get_lower(self):
        """Suitedness is worth more to hands that need a flush to win."""
        grid = heat.suited_edge_grid(self.table, 1)
        high = grid[0][3]   # AJ
        low = grid[10][12]  # 42
        self.assertGreater(low, high)


if __name__ == "__main__":
    unittest.main()
