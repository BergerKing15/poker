#!/usr/bin/env python3
"""Precompute pre-flop equity for every starting hand and opponent count.

There are only 169 distinct starting hands, so 169 x 9 opponent counts covers
every pre-flop decision the bots can ever face. Building it once removes the
largest runtime cost in the project.

The work is embarrassingly parallel and heavily skewed — a nine-opponent cell
costs roughly five times a heads-up one — so cells are handed to a process pool
longest-first to keep every worker busy to the end.

    python -m tools.build_equity_table --simulations 2000
"""

import argparse
import os
import time
from multiprocessing import Pool

from poker.config import PREFLOP_TABLE_PATH
from poker.console import enable_utf8_output
from poker.equity import WinProbabilityCalculator
from poker.equity_cache import RESULT_FIELDS, save_preflop_table
from poker.notation import all_preflop_keys, cards_for_key

MAX_OPPONENTS = 9


def _cell(job):
    """Compute one (hand, opponents) cell. Runs in a worker process."""
    key, opponents, simulations = job
    calculator = WinProbabilityCalculator(num_simulations=simulations)
    result = calculator.calculate_win_probability(
        cards_for_key(key), [], opponents
    )
    return key, opponents, [round(result[field], 5) for field in RESULT_FIELDS]


def build(simulations: int, processes: int, max_opponents: int = MAX_OPPONENTS):
    keys = all_preflop_keys()
    # Longest jobs first: more opponents means more hands evaluated per sample.
    jobs = [(key, opponents, simulations)
            for opponents in range(max_opponents, 0, -1)
            for key in keys]

    table = {key: {} for key in keys}
    started = time.time()
    done = 0

    with Pool(processes=processes) as pool:
        for key, opponents, values in pool.imap_unordered(_cell, jobs, chunksize=4):
            table[key][str(opponents)] = values
            done += 1
            if done % 100 == 0 or done == len(jobs):
                elapsed = time.time() - started
                rate = done / elapsed
                remaining = (len(jobs) - done) / rate if rate else 0
                print(f"  {done:5}/{len(jobs)} cells  "
                      f"{elapsed:6.1f}s elapsed  ~{remaining:5.1f}s remaining",
                      flush=True)

    return table, len(jobs), time.time() - started


def main():
    enable_utf8_output()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--simulations", type=int, default=2000,
                        help="Monte Carlo samples per cell (default: 2000)")
    parser.add_argument("--processes", type=int, default=max(os.cpu_count() - 1, 1),
                        help="worker processes (default: CPU count minus one)")
    parser.add_argument("--max-opponents", type=int, default=MAX_OPPONENTS)
    args = parser.parse_args()

    print(f"Building pre-flop equity table: {len(all_preflop_keys())} hands x "
          f"{args.max_opponents} opponent counts")
    print(f"  {args.simulations} simulations per cell, {args.processes} processes")
    print(f"  standard error is roughly {0.5 / args.simulations ** 0.5:.4f}")
    print()

    table, cells, elapsed = build(args.simulations, args.processes, args.max_opponents)
    save_preflop_table(table, args.simulations)

    size_kb = PREFLOP_TABLE_PATH.stat().st_size / 1024
    print()
    print(f"Wrote {cells} cells to {PREFLOP_TABLE_PATH} ({size_kb:.0f} KB) "
          f"in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
