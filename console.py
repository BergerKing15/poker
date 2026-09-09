"""Console helpers shared by the command-line entry points."""

import sys


def enable_utf8_output() -> None:
    """Allow this process to print the check marks and emoji the scripts use.

    Windows defaults stdout to cp1252, which raises UnicodeEncodeError part way
    through a run and buries the real results under a traceback. Reconfiguring
    to UTF-8 keeps the output readable; errors="replace" means an exotic glyph
    on a legacy console degrades to a placeholder instead of killing the run.

    Safe to call more than once, and a no-op on streams that cannot be
    reconfigured (a StringIO put in place by a test harness, for instance).
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass
