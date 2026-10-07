"""Application behavior layered over the core save widget."""

import sys

# 3rd party imports
from Qt import QtCore, QtGui, QtWidgets
from necessities import assemble as _assemble

# Package imports
from nscene.widgets.main_widget import FormedNukeContextDialog as _FormedNukeContextDialog
from nscene.widgets.script_tree import ExistingScriptsTreeView


class NukeSaveAsInterface:
    """Control the application behavior for a standalone base dialog."""

    def __init__(self, parent=None):
        self._base_widget = _FormedNukeContextDialog(parent)
        self.scene_assembler = _assemble.Scene.from_application("nuke", root="/vfx/wgid/projects")

    def save(self) -> bool:
        """Save the current scene in the host application."""
        # Host-specific save behavior can be layered here.
        # Create the folder if it doesn't exist.
        import nuke

        preview_path = self._base_widget.get_preview_path()
        directory = QtCore.QFileInfo(preview_path).absolutePath()
        if not QtCore.QDir(directory).exists():
            QtCore.QDir().mkpath(directory)

        # Use touch to create an empty file if it doesn't exist.
        file_path = preview_path
        nuke.scriptSaveAs(file_path)

        return True


def load():
    """Create and run the interface in a standalone Qt application."""
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    view = NukeSaveAsInterface()
    app.exec()
    return view


def load_in_application():
    """Show the interface in an existing host application."""
    view = NukeSaveAsInterface()
    return view


load()