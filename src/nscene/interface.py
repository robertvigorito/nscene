"""Public entry points for the Nuke Open and Save interfaces."""

from nscene import open_interface as _open_interface
from nscene import save_as_interface as _save_interface
from nscene.open_interface import NukeOpenInterface
from nscene.save_as_interface import (
    NSaveInterface,
    NSaveView,
    NukeSaveAsInterface,
    load,
)


def open_in_application() -> NukeOpenInterface:
    """Create and show the Open interface inside the host application."""
    return _open_interface.load_in_application()


def save_in_application() -> NukeSaveAsInterface:
    """Create and show the Save interface inside the host application."""
    return _save_interface.load_in_application()


# Keep the original Save entry point available for existing callers.
load_in_application = save_in_application

__all__ = [
    "NSaveInterface",
    "NSaveView",
    "NukeOpenInterface",
    "NukeSaveAsInterface",
    "load",
    "load_in_application",
    "open_in_application",
    "save_in_application",
]
