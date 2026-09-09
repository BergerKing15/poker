# CLAUDE.md

Texas Hold'em poker engine + Tkinter GUI + bot tournament harness. Pure Python, no
package manifest — dependencies are stdlib plus `Pillow` (GUI only). Python 3.11/3.12
in CI; 3.13 works locally.

## Commands

```bash
python poker_ui.py            # play the GUI game (Tkinter + Pillow required)
python tournament_ui.py       # tournament dashboard GUI
python bot_tourney.py         # full headless bot tournament -> tournament_results.json
python bot_tourney.py --fast  # same, but every AI bot is swapped for "Random" (seconds, not minutes)
python bot_tourney.py --ui    # tournament with the analytics dashboard
python verify_installation.py # smoke check: imports, bot types, game creation
python all_tests.py           # all 3 suites (~0.05s)
```

Individual suites: `game_test_suite.py`, `win_probability_test_suite.py`, `test_bot_ai.py`,
`test_all_bots.py` (bot registry), `test_tourney_quick.py` (short tournament).

**On Windows, prefix test/tournament commands with `PYTHONIOENCODING=utf-8`.** Every script
prints `✓`/`❌`/emoji, and the default cp1252 console encoding makes them die with
`UnicodeEncodeError` before any test result is reported — the failure looks like a test
failure but isn't.

## Architecture

- `poker_game.py` — the engine. `Card`/`Deck`, `HandEvaluator` (static, evaluates all
  C(7,5) combos), `Player`, and `PokerGame` (blinds, betting rounds, side pots, showdown).
  Headless; `PokerGame.DEBUG` gates all its printing.
- `poker_bot.py` — `PokerBot` (equity + position + pot-odds decisions, 5 styles in
  `PokerBot.TYPES`: TAG/LAG/CTR/NIT/FISH), `BotManager`, and 12 `SimpleBot*` fixed-strategy
  baselines used as tournament controls / ML training opponents.
- `win_probability.py` — `WinProbabilityCalculator.calculate_win_probability()`, Monte
  Carlo, returns `{win_prob, tie_prob, lose_prob, equity}`. This is the hot path in any
  tournament involving `PokerBot`s.
- `poker_ui.py` — `PokerUI`. Runs the hand loop on a daemon thread and blocks on human
  input via `self.current_player_action`.
- `bot_tourney.py` — `BotTournament`, plus `ProgressTracker` (background thread, prints
  progress every N seconds). `tournament_ui.py` is the GUI equivalent.
- `config.py` — all tunable constants (window size, blinds, `NUM_SIMULATIONS_SETUP`,
  `ENABLE_DEBUG`). Prefer adding constants here over inlining literals.
- `cards-png-100px/` — card images, one per `<rank><suit-initial>.png` (`10D.png`, `AS.png`).
  Public-domain Vector Playing Cards; don't regenerate.

Docs in [docs/](docs/) are design notes written alongside features; they lag the code, so
trust the source when they disagree.

### Two independent hand loops

`PokerGame.play_hand()`/`betting_round()` drive headless play (tests, tournaments), and
`PokerUI.play_single_hand()`/`PokerUI.betting_round()` are a *separate reimplementation*
for the GUI (it needs to interleave logging, display updates, and blocking on the human).
A change to betting/street logic almost always has to be made in both places, or the GUI
and the tournament results silently diverge.

### How a bot gets consulted

`PokerGame.ai_decision` → `_bot_decision` looks up `self.bots[player_id]` and calls
`decide_action(...)`, which returns `(action, raise_amount)`. The betting loop only
handles the string action, so a raise amount is smuggled through `self.pending_raise_amount`
and cleared on read.

Any bot class just needs `decide_action(hole_cards, community_cards, current_bet, to_call,
player_stack, pot, position, num_opponents, small_blind, big_blind)` — the `SimpleBot*`
classes are plain classes, not `PokerBot` subclasses. Register new ones in
`BotTournament.BOT_FACTORY` (keyed by the string used in tournament configs).

Note the two ways bots get assigned: `PokerGame(bot_types={player_id: "TAG"})` maps
**int player_id → type string** and only ever builds `PokerBot`s (player 0 is skipped as
the human). Tournaments bypass this entirely — `_run_single_game` constructs the game and
then overwrites `game.bots` with factory-built instances for *every* seat including 0.

**`_bot_decision` wraps the bot call in a bare `except Exception` and silently falls back
to `_simple_ai_decision`.** A crashing bot therefore shows up as mediocre tournament
results rather than a traceback. When a bot behaves oddly, set `PokerGame.DEBUG = True`
to see the swallowed error, or call `decide_action` directly.

## Known traps

- **Ranks are `'10'`, not `'T'`.** `Card.RANKS` uses the two-character `'10'`. The
  `_get_hand_key` helpers duplicated across the `SimpleBot*` classes use a `rank_order`
  dict keyed on `'T'`, so any hole card that is a ten raises `KeyError: '10'` — swallowed
  by the fallback above. Fix the maps (or the card representation) rather than working
  around it; the same map is copy-pasted in several bot classes.
- **`.github/workflows/tests.yml` contains constructor calls that no longer match the
  code** — `PokerBot('TAG', tightness=…, aggression=…)` (the real signature is
  `PokerBot(player_id, bot_type)`), `SimpleBotTop10Percent()` with no `player_id`, and
  `bot_types={'Player 1': <bot instance>}` (keys must be ints, values type strings).
  Several test steps also swallow failures with `|| echo "✓ … completed"`. Treat a green
  badge as weak evidence; run the suites locally.
- `run_simple_tournament.py` and `run_large_tournament.py` start with a hardcoded
  `sys.path.insert(0, '/home/noahberg/Projects/PokerAI')` — harmless but dead on this
  machine; they only work when run from the repo root.
- `all_tests.py` "runs" suites by *importing* them (the tests execute at module import).
  A suite that is already imported in the same process is a no-op, and a suite that
  passes without asserting anything still reports PASSED.
- `poker/` is a stray nested clone containing only `.git`; the working tree here is not
  itself a git repo.

## Conventions

- No test framework — suites are plain scripts using `GameTester`'s `assert_*` helpers
  (`game_test_suite.py`), which tally results and print a summary. Add cases as
  `test_*()` functions and call them from that file's `__main__` block; nothing
  auto-discovers them.
- To test engine behaviour deterministically, use `GameScript` + `MockPokerGame` from
  `game_test_suite.py`: they let you pin hole cards, community cards, and a per-street
  action sequence. `GameTester.parse_hand("AS KS")` builds cards from strings.
- Print only behind `DEBUG` / `config.ENABLE_DEBUG` in engine and UI code; CI greps for
  unguarded `print(` in `poker_game.py`, `poker_ui.py`, `config.py`.
- Type hints are used on newer engine/bot code (`Optional[...]`, `List[Card]`); match the
  surrounding file.
