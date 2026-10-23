"""Application behavior layered over the core save widget."""

import sys

from necessities import assemble as _assemble

# 3rd party imports
from Qt import QtCore, QtWidgets

# Package imports
from nscene.paths import get_projects_root
from nscene.widgets.main_widget import FormedNukeContextDialog as _FormedNukeContextDialog


class NukeSaveAsInterface:
    """Control the application behavior for a standalone base dialog."""

    def __init__(self, parent=None):
        projects_root = get_projects_root()
        self._base_widget = _FormedNukeContextDialog(parent, projects_root=projects_root)
        self.scene_assembler = _assemble.Scene.from_application("nuke", root=projects_root)

    @property
    def base_widget(self):
        """Return the shared save dialog."""
        return self._base_widget.base_widget

    def show(self):
        """Show the save dialog."""
        self._base_widget.show()

    def close(self):
        """Close the save dialog."""
        self._base_widget.close()

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
        self.close()

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


NSaveInterface = NukeSaveAsInterface
NSaveView = NukeSaveAsInterface
