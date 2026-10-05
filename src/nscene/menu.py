"""Nuke menu hook for nscene.

Nuke discovers this module when NUKE_PATH includes the installed nscene package
folder. The command shows Rez context variables for quick validation.
"""

from __future__ import annotations

import os


def _is_rez_context() -> bool:
    return bool(os.getenv("REZ_USED_REQUEST") or os.getenv("REZ_USED_RESOLVE"))


def _register_menu() -> None:
    import nuke

    main_menu = nuke.menu("Nuke")
    nscene_menu = main_menu.addMenu("NSCENE")
    nscene_menu.addCommand(
        "Rez Context Test",
        "import nscene.rez_menu_test as _nscene_rez_test; _nscene_rez_test.show_rez_context()",
    )


if _is_rez_context():
    try:
        _register_menu()
    except Exception:
        # Avoid blocking Nuke startup if menu registration fails.
        pass


_register_menu()