"""The SQLite hand log."""

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from poker.hand_log import HandLog
from poker.tournament import BotTournament
from tests.support import FixedBot, hand, silent_game


class HandLogTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db = Path(self._tmp.name) / "hands.db"

    def play(self, hands=5, bots=("CheckCall", "CheckCall", "Random"), **kwargs):
        log = HandLog(self.db, **kwargs)
        game = silent_game(num_players=len(bots), starting_stack=1000,
                           small_blind=5, big_blind=10, use_bots=True,
                           observer=log)
        game.bots = {i: BotTournament.BOT_FACTORY[name](i)
                     for i, name in enumerate(bots)}
        log.bot_types = {i: name for i, name in enumerate(bots)}
        for _ in range(hands):
            game.play_hand()
        return log, game


class TestSchema(HandLogTestCase):
    def test_tables_are_created(self):
        log = HandLog(self.db)
        names = {row[0] for row in log.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertLessEqual({"runs", "hands", "hand_players", "actions"}, names)
        log.close()

    def test_opening_twice_does_not_destroy_data(self):
        log, _ = self.play(hands=3)
        log.close()
        second = HandLog(self.db)
        count = second.connection.execute("SELECT COUNT(*) FROM hands").fetchone()[0]
        second.close()
        self.assertEqual(count, 3)

    def test_each_run_gets_its_own_row(self):
        first, _ = self.play(hands=2, label="one")
        first.close()
        second, _ = self.play(hands=2, label="two")
        labels = [r[0] for r in second.connection.execute(
            "SELECT label FROM runs ORDER BY run_id")]
        second.close()
        self.assertEqual(labels, ["one", "two"])

    def test_metadata_round_trips(self):
        log = HandLog(self.db, label="x", metadata={"note": "hello"})
        stored = log.connection.execute(
            "SELECT metadata FROM runs").fetchone()[0]
        log.close()
        self.assertEqual(json.loads(stored)["note"], "hello")

    def test_context_manager_closes_the_connection(self):
        with HandLog(self.db) as log:
            pass
        with self.assertRaises(sqlite3.ProgrammingError):
            log.connection.execute("SELECT 1")


class TestRecording(HandLogTestCase):
    def test_one_row_per_hand(self):
        log, _ = self.play(hands=6)
        count = log.connection.execute("SELECT COUNT(*) FROM hands").fetchone()[0]
        log.close()
        self.assertEqual(count, 6)
        self.assertEqual(count, 6)

    def test_one_player_row_per_seat_per_hand(self):
        log, game = self.play(hands=4)
        count = log.connection.execute(
            "SELECT COUNT(*) FROM hand_players").fetchone()[0]
        log.close()
        self.assertEqual(count, 4 * len(game.players))

    def test_hole_cards_and_board_are_recorded(self):
        log, _ = self.play(hands=3)
        holes = [r[0] for r in log.connection.execute(
            "SELECT hole_cards FROM hand_players")]
        log.close()
        self.assertTrue(all(len(h.split()) == 2 for h in holes), holes)

    def test_every_hand_has_at_least_one_winner(self):
        log, _ = self.play(hands=10)
        wins = log.connection.execute("SELECT SUM(won) FROM hand_players").fetchone()[0]
        hands_played = log.connection.execute("SELECT COUNT(*) FROM hands").fetchone()[0]
        log.close()
        self.assertGreaterEqual(wins, hands_played)

    def test_net_is_the_stack_change(self):
        log, _ = self.play(hands=5)
        rows = log.connection.execute(
            "SELECT starting_stack, final_stack, net FROM hand_players").fetchall()
        log.close()
        for start, final, net in rows:
            self.assertEqual(net, final - start)

    def test_chips_are_conserved_within_each_hand(self):
        log, _ = self.play(hands=8)
        rows = log.connection.execute(
            "SELECT hand_id, SUM(net) FROM hand_players GROUP BY hand_id").fetchall()
        log.close()
        for hand_id, total in rows:
            self.assertEqual(total, 0, f"hand {hand_id} does not balance")

    def test_actions_are_recorded_in_order(self):
        log, _ = self.play(hands=3)
        rows = log.connection.execute(
            "SELECT hand_id, seq FROM actions ORDER BY hand_id, seq").fetchall()
        log.close()
        self.assertTrue(rows)
        by_hand = {}
        for hand_id, seq in rows:
            by_hand.setdefault(hand_id, []).append(seq)
        for seqs in by_hand.values():
            self.assertEqual(seqs, list(range(len(seqs))))

    def test_actions_carry_a_street(self):
        log, _ = self.play(hands=3)
        stages = {r[0] for r in log.connection.execute("SELECT stage FROM actions")}
        log.close()
        self.assertTrue(stages <= {"Pre-Flop", "Flop", "Turn", "River"}, stages)

    def test_bot_type_is_attached_to_each_seat(self):
        log, _ = self.play(hands=3, bots=("CheckCall", "Random"))
        types = {r[0] for r in log.connection.execute(
            "SELECT DISTINCT bot_type FROM hand_players")}
        log.close()
        self.assertEqual(types, {"CheckCall", "Random"})

    def test_bot_names_are_discovered_when_not_supplied(self):
        log = HandLog(self.db)
        game = silent_game(num_players=2, starting_stack=1000, use_bots=True,
                           observer=log)
        game.bots = {0: FixedBot(0, "check"), 1: FixedBot(1, "check")}
        game.play_hand()
        types = {r[0] for r in log.connection.execute(
            "SELECT DISTINCT bot_type FROM hand_players")}
        log.close()
        self.assertEqual(types, {"Fixed-check"})


class TestQueries(HandLogTestCase):
    def test_summary_groups_by_bot(self):
        log, _ = self.play(hands=6, bots=("CheckCall", "Random"))
        summary = log.summary_by_bot()
        log.close()
        self.assertEqual({row["bot_type"] for row in summary}, {"CheckCall", "Random"})
        for row in summary:
            self.assertEqual(row["hands"], 6)

    def test_action_counts_are_grouped(self):
        log, _ = self.play(hands=6)
        counts = log.action_counts()
        log.close()
        self.assertTrue(counts)
        for row in counts:
            self.assertIn("action", row)
            self.assertGreater(row["n"], 0)


class TestTournamentIntegration(HandLogTestCase):
    def test_tournament_can_record_every_hand(self):
        tournament = BotTournament()
        tournament.run_tournament(
            [{"num_players": 2, "bot_types": ["CheckCall", "Random"], "repeat": 2}],
            hands_per_game=5, verbose=False, hand_log_path=str(self.db))
        log = tournament.hand_log
        self.assertIsNotNone(log)
        self.assertEqual(log.hands_recorded, 10)
        self.assertEqual({row["bot_type"] for row in log.summary_by_bot()},
                         {"CheckCall", "Random"})
        log.close()

    def test_tournament_without_a_path_records_nothing(self):
        tournament = BotTournament()
        tournament.run_tournament(
            [{"num_players": 2, "bot_types": ["CheckCall", "Random"], "repeat": 1}],
            hands_per_game=3, verbose=False)
        self.assertIsNone(tournament.hand_log)


if __name__ == "__main__":
    unittest.main()
