# CLAUDE.md

Texas Hold'em poker engine + Tkinter GUI + bot tournament harness. Pure Python, no
package manifest — dependencies are stdlib plus `Pillow` (GUI only). Python 3.11/3.12
in CI; 3.13 works locally.

## Commands

Run everything from the repo root; the package is imported as `poker`, not installed.

```bash
python play.py                  # play the GUI game (Tkinter + Pillow required)
python run_tournament.py        # headless bot tournament -> tournament_results.json
python run_tournament.py --ui   # tournament with the analytics dashboard
python run_tournament.py --log hands.db   # record every hand to SQLite
python -m tools.verify_installation       # smoke check: imports, bot types, game creation
python -m tools.check_prints              # fail on prints outside a DEBUG guard
python -m tools.build_equity_table        # precompute the pre-flop equity table
```

### Tests

```bash
python -m unittest discover -s tests -t .   # the whole suite, ~2.5 min
```

`-t .` sets the top-level directory so `poker` and `tests.support` import; discovery
fails without it. While iterating, narrow instead of running everything:

```bash
python -m unittest tests.test_betting                    # one module
python -m unittest tests.test_betting.TestMinimumRaise   # one class
python -m unittest discover -s tests -t . -k raise       # substring match
python -m unittest discover -s tests -t . -k '*Notation*'  # glob
```

`-k` matches the **method** name, not the class, so `-k notation` runs nothing while
`-k '*Notation*'` runs eight. "NO TESTS RAN" usually means that. `-v` lists names, `-f`
stops at the first failure.

Most modules finish in seconds; `test_betting` (~100s) and `test_equity` (~190s) are slow
because they sample. Run the module you are touching, and the full discover before
committing.

Every entry point calls `poker.console.enable_utf8_output()` before printing, which keeps
the `✓`/emoji output from dying with `UnicodeEncodeError` on a cp1252 Windows console.
Call it first in any new script that prints non-ASCII; without it the traceback lands
mid-run and looks like a test failure.

## Architecture

```
poker/          engine, bots, equity, tournament runner
poker/ui/       Tk front-ends
tests/          unittest suite
tools/          check_prints, verify_installation, build_equity_table, diagnose_hang
scripts/        ready-made tournament runs
assets/         card images
play.py, run_tournament.py    launchers
```

- `poker/game.py` — the engine. `Card`/`Deck`, `HandEvaluator` (static, evaluates all
  C(7,5) combos), `Player`, `PokerGame` (blinds, betting, side pots, showdown), and the
  `GameObserver` / `ConsoleObserver` / `GameAborted` front-end contract. Headless;
  `PokerGame.DEBUG` gates its printing.
- `poker/bot.py` — `PokerBot` (equity + position + pot-odds decisions, 5 styles in
  `PokerBot.TYPES`: TAG/LAG/CTR/NIT/FISH), `BotManager`, `raise_to_total`, and 12
  `SimpleBot*` fixed-strategy baselines used as tournament controls.
- `poker/notation.py` — starting-hand notation (`hand_key`, `preflop_key`, `RANK_VALUES`,
  `all_preflop_keys`, `cards_for_key`). Depends only on `poker.game`, so both `poker.bot`
  and `poker.equity_cache` can use it without an import cycle. `poker.bot` re-exports
  `hand_key`/`RANK_VALUES` for callers that already referred to them there.
- `poker/equity.py` — `WinProbabilityCalculator.calculate_win_probability()`, Monte Carlo,
  returns `{win_prob, tie_prob, lose_prob, equity}`, plus `get_hand_strength` category
  bands. The hot path in any tournament involving `PokerBot`s.
- `poker/equity_cache.py` — `CachedEquityCalculator`, a drop-in for the above. Answers
  pre-flop from a precomputed table and memoises post-flop for the process. `PokerBot`'s
  shared calculator is one of these.
- `poker/hand_log.py` — `HandLog`, a `GameObserver` that writes one row per player per
  hand plus the action sequence to SQLite, and `FanOutObserver` for attaching it
  alongside a front-end.
- `poker/tournament.py` — `BotTournament` (`BOT_FACTORY` registry, optional
  `hand_log_path`) and `ProgressTracker`.
- `poker/config.py` — tunable constants plus `PROJECT_ROOT`/`ASSETS_DIR`/`CARDS_DIR`/
  `PREFLOP_TABLE_PATH`, resolved from `__file__` so paths hold whatever the working
  directory is. Prefer adding constants here over inlining literals.
- `poker/ui/game_window.py` — `PokerUI`. Runs the hand loop on a daemon thread and blocks
  on human input via `self.current_player_action`. `poker/ui/tournament_window.py` is the
  analytics dashboard.
- `assets/cards-png-100px/` — card images, one per `<rank><suit-initial>.png` (`10D.png`).
  Public-domain Vector Playing Cards; don't regenerate.

Docs in [docs/](docs/) are design notes written alongside features; they lag the code, so
trust the source when they disagree.

### One hand loop, driven through hooks

`PokerGame.play_hand()` / `betting_round()` is the only betting implementation.
A front-end supplies a `GameObserver` (`poker/game.py`) and the engine calls its hooks:
`on_hand_start`, `on_blinds`, `on_stage`, `before_ai_action`, `get_human_action`,
`on_action`, `on_turn_advanced`, `on_showdown`, `on_hand_end`. Every hook defaults to a
no-op, so tournaments and tests pass no observer at all; a bare `PokerGame` gets
`ConsoleObserver`, which keeps the terminal demo in `__main__` working.

`PokerUI` subclasses `GameObserver` and passes `observer=self`, so the GUI has no betting
loop of its own — it renders `on_action` and blocks in `get_human_action` until a button
is pressed. Two things worth knowing when writing an observer:

- **A misspelled hook silently becomes a no-op**, since the base class defines them all.
  `tests/test_observer.py` asserts `PokerUI` overrides every hook — extend it if you
  add one.
- `get_human_action` returns `(action, raise_amount)` and may raise `GameAborted` to
  abandon the hand (the UI does this when its window closes). `before_ai_action` returning
  `False` defers that bot to a later pass, which is how "skip to my turn" works.

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

- **Ranks are `'10'`, not `'T'`.** `Card.RANKS` spells ten as the two-character `'10'`,
  but starting-hand notation (and every `SimpleBot*` range constant — `'TT'`, `'AT'`,
  `'T9o'`) uses `'T'`. Go through `poker.notation.hand_key()` / `RANK_VALUES`, which accept
  both and fold `'10'` → `'T'`; don't hand-roll another rank map. This previously raised
  `KeyError: '10'` on any ten, silently swallowed by the fallback above.
- CI has no failure-swallowing left (`|| echo "… completed"` guards are gone) and every
  step propagates its exit code, so a red badge now means something.
  `python -m tools.check_prints` enforces the print-behind-DEBUG convention with an AST
  walk and a documented allowlist — plain grep matched the `__main__` demos and warned on
  every run.
- Everything is run from the repo root: the package is imported as `poker`, not
  installed, so `python -m tools.x` and `python play.py` work while running a file from
  inside `tools/` or `scripts/` does not.
- Starting-range constants (`TOP_10_PERCENT`, `BOTTOM_50_PERCENT`, `PREMIUM_HANDS`,
  `EARLY_HANDS`/`LATE_HANDS`) must be written in the same high-card-first notation
  `hand_key()` emits, or the entry is simply unreachable and the bot never plays it.
  `tests/test_bots.py::TestBotRanges` enforces this across every range constant it can
  find, so a low-card-first typo fails the suite instead of quietly shrinking a range.
- A raise is expressed as a **total to raise the round bet TO**, never an increment —
  the same thing the log means by "raises to $60". `PokerGame._apply_raise` clamps it to
  `minimum_raise_to()` and to the player's stack, so passing a huge number means all-in.
  Bots build totals with `poker.bot.raise_to_total(current_bet, to_call, stack, extra)`.
- Equity assertions are Monte Carlo. `WinProbabilityTester` seeds per instance for
  reproducibility, but where a hand's true equity sits within a standard error or two of
  a `get_hand_strength` category edge, assert with `assert_hand_strength_in` and a set of
  acceptable labels — pinning one label there tests the sampler's luck, not the code.
- Side pots are built from **whole-hand** contributions (`total_bet_by_player`, via
  `_contributions()`), not `total_bet_this_round`, which `reset_round_bets` clears every
  street — reading the latter meant showdown saw only the river's betting and the rest of
  the pot went to nobody. `_contributions()` falls back to the street bet for any player
  nothing was recorded for, which is how tests build scenarios by assigning
  `total_bet_this_round` directly. A folded player's chips stay in the pot as dead money;
  they are simply not eligible to win it.

## Outstanding work

Nothing outstanding from the last round. Worth knowing for whatever comes next:

- `poker/data/preflop_equity.json` is a committed build artifact: 1521 cells at 10,000
  simulations, about 0.005 standard error, built by
  `python -m tools.build_equity_table --simulations 10000` in roughly an hour across 11
  workers. Rebuild it only to change the sample size; it is deterministic given that
  count. Background it with a runner that keeps the parent alive — a detached shell `&`
  kills the coordinator and the workers finish into nothing. The builder's own ETA is
  linear and so badly pessimistic: work runs longest-first (all nine-opponent cells,
  then eight, down to heads-up), so the rate rises throughout.
- Bots are now **deterministic pre-flop**, since equity comes from the table rather than
  a fresh sample. Reproducible, but tournament numbers from before the table are not
  comparable with numbers from after it.
- `docs/` still describes the pre-reorganisation layout and the deleted root suite. Those
  are historical design notes, not instructions; trust the source.

## Conventions

- New tests are `unittest` under `tests/`, discovered by name. Shared helpers live in
  `tests/support.py`: `card()`/`hand()` build cards from shorthand (`hand("AS 10D")`),
  `silent_game()` returns a game whose observer does nothing so tests never block on
  `input()`, `ScriptedObserver` stands in for a front-end, `FixedBot` always returns one
  action, and `GameScript`/`ScriptedGame` pin the cards dealt.
- Equity assertions are Monte Carlo, so bound them on the measured value with room for
  noise (~0.007 std error at 5,000 simulations, ~0.01 at 2,500); a bound hugging the true
  value within ~3σ will flake. Where a hand's real equity sits within a standard error of
  a `get_hand_strength` category edge, assert a set of acceptable labels instead of one —
  pinning one there tests the sampler's luck. Seed for reproducibility.
- Print only behind `DEBUG` / `config.ENABLE_DEBUG` in engine code; `tools/check_prints.py`
  enforces it over `poker/game.py`, `poker/bot.py`, `poker/equity.py`, `poker/config.py`
  with a documented allowlist.
- Type hints are used on newer engine/bot code (`Optional[...]`, `List[Card]`); match the
  surrounding file.
