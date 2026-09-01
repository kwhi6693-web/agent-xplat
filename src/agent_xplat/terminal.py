"""Small terminal helpers used by the CLI."""

from __future__ import annotations

import sys


def emit(text: str, output: str | None = None) -> None:
    if output:
        with open(output, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    else:
        sys.stdout.write(text)
