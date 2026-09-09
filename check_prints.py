#!/usr/bin/env python3
"""Enforce the "print only behind DEBUG" convention in engine modules.

Plain grep cannot do this usefully: it matches the console demos under
`if __name__ == "__main__"` and the interactive prompts, so it warned on every
run and the warning stopped meaning anything.
"""

import ast
import sys

from console import enable_utf8_output

# Modules that must not print during normal operation.
CHECKED = ["poker_game.py", "poker_bot.py", "win_probability.py", "config.py"]

# Prints that are the program's actual output rather than stray logging.
# ("file", "enclosing function") -> why it is allowed.
ALLOWED = {
    ("poker_game.py", "get_human_action"):
        "ConsoleObserver's terminal prompt - this is the front-end's own "
        "output, not stray logging from the engine",
}


def offending_prints(path):
    """Yield (lineno, enclosing_function) for prints that need a DEBUG guard."""
    tree = ast.parse(open(path, encoding="utf-8").read())

    # Skip `if __name__ == "__main__":` blocks - those are console demos.
    top_level = [n for n in tree.body
                 if not (isinstance(n, ast.If) and "__name__" in ast.dump(n.test))]

    for node in top_level:
        for func in [n for n in ast.walk(node) if isinstance(n, ast.FunctionDef)] or [node]:
            guarded = set()
            for branch in ast.walk(func):
                if isinstance(branch, ast.If) and "DEBUG" in ast.dump(branch.test):
                    guarded.update(id(c) for c in ast.walk(branch))
            for call in ast.walk(func):
                if (isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
                        and call.func.id == "print" and id(call) not in guarded):
                    name = func.name if isinstance(func, ast.FunctionDef) else "<module>"
                    yield call.lineno, name


def main():
    enable_utf8_output()
    violations = []
    for path in CHECKED:
        for lineno, func in offending_prints(path):
            if (path, func) in ALLOWED:
                continue
            violations.append(f"{path}:{lineno} in {func}()")

    if violations:
        print("Unguarded print statements found (wrap in `if self.DEBUG:` or")
        print("add to ALLOWED in check_prints.py with a reason):")
        for v in violations:
            print(f"  {v}")
        return 1

    print(f"No unguarded prints in {len(CHECKED)} engine modules "
          f"({len(ALLOWED)} documented exception(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
