"""Helpers for validating Nuke menu injection from a Rez context."""

from __future__ import annotations

import os


def _rez_info_lines() -> list[str]:
    keys = [
        "NSCENE_REZ_MENU_TEST",
        "REZ_USED_REQUEST",
        "REZ_USED_RESOLVE",
        "REZ_CONTEXT_FILE",
    ]
    lines = ["NSCENE Rez Menu Test"]
    for key in keys:
        value = os.getenv(key, "<not set>")
        lines.append(f"{key}: {value}")
    return lines


def show_rez_context() -> None:
    """Show rez context values from inside Nuke."""
    message = "\n".join(_rez_info_lines())

    try:
        import nuke

        nuke.message(message)
    except Exception:
        # If nuke UI is unavailable, still emit useful output.
        print(message)
