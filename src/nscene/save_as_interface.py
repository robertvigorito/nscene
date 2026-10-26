"""Application behavior layered over the core save widget."""

import sys

from necessities import assemble as _assemble

# 3rd party imports
from Qt import QtCore, QtWidgets

# Package imports
from nscene.paths import get_projects_root, normalize_platform_path
from nscene.widgets.main_widget import FormedNukeContextDialog as _FormedNukeContextDialog


class NukeSaveAsInterface:
    """Control the application behavior for a standalone base dialog."""

    def __init__(self, parent=None):
        projects_root = get_projects_root()
        self._base_widget = _FormedNukeContextDialog(parent, projects_root=projects_root)
        self.scene_assembler = _assemble.Scene.from_application("nuke", root=projects_root)
        widget = self._base_widget.base_widget
        widget.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnTopHint, True)
        for field in (widget.project_edit, widget.sequence_edit, widget.shot_edit, widget.description_edit):
            field.textChanged.connect(self._update_preview)
        widget.version_edit.valueChanged.connect(self._update_preview)
        widget.minor_version_edit.valueChanged.connect(self._update_preview)
        widget.save_button.clicked.connect(lambda _checked=False: self.save())
        widget.clear_script_button.clicked.connect(lambda _checked=False: self.clear_script_and_save_as())
        widget.paste_selected_action.triggered.connect(lambda _checked=False: self.paste_selected_script())
        self._update_preview()
        widget.show()

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

    def _update_preview(self, *_args: object) -> bool:
        """Build and display the target script path from the current form values.

        Args:
            *_args: Signal arguments, which are unused.

        Returns:
            True when a complete path was generated, otherwise False.
        """
        settings = self._base_widget.get_settings()
        widget = self._base_widget.base_widget
        if not all((settings.project, settings.description)):
            self._base_widget.set_preview_path("")
            widget.save_button.setEnabled(False)
            return False

        scene = self.scene_assembler.replace(
            show=settings.project,
            sequence=settings.sequence,
            shot=settings.shot,
            description=settings.description,
            version=settings.version,
            minor_version=settings.minor_version,
        )
        preview_path = normalize_platform_path(QtCore.QDir.cleanPath(scene.resolve()))
        self._base_widget.set_preview_path(preview_path)
        widget.script_tree.set_save_path(preview_path)
        widget.save_button.setEnabled(True)
        return True

    def save(self) -> bool:
        """Save the current scene in the host application."""
        preview_path = self._base_widget.get_preview_path()
        if not preview_path:
            return False

        directory = QtCore.QFileInfo(preview_path).absolutePath()
        if not QtCore.QDir().mkpath(directory):
            QtWidgets.QMessageBox.warning(
                self._base_widget.base_widget,
                "Save As failed",
                f"Could not create the directory:\n{directory}",
            )
            return False

        try:
            import nuke

            nuke.scriptSaveAs(preview_path)
        except (ImportError, OSError, RuntimeError) as error:
            QtWidgets.QMessageBox.warning(
                self._base_widget.base_widget,
                "Save As failed",
                f"Could not save the Nuke script:\n{error}",
            )
            return False

        self.close()
        return True

    def clear_script_and_save_as(self) -> bool:
        """Clear the current Nuke script and save an empty script to the preview path.

        Returns:
            True when the cleared script was saved successfully, otherwise False.
        """
        preview_path = self._base_widget.get_preview_path()
        if not preview_path:
            return False

        directory = QtCore.QFileInfo(preview_path).absolutePath()
        if not QtCore.QDir().mkpath(directory):
            QtWidgets.QMessageBox.warning(
                self._base_widget.base_widget,
                "Clear and Save As failed",
                f"Could not create the directory:\n{directory}",
            )
            return False

        try:
            import nuke

            nuke.scriptClear()
        except (AttributeError, ImportError, OSError, RuntimeError, ValueError) as error:
            QtWidgets.QMessageBox.warning(
                self._base_widget.base_widget,
                "Clear and Save As failed",
                f"Could not clear the Nuke script:\n{error}",
            )
            return False

        return self.save()

    def paste_selected_script(self) -> bool:
        """Paste the selected script's nodes into the current Nuke node graph.

        Returns:
            True when the selected script was pasted successfully, otherwise False.
        """
        tree = self._base_widget.base_widget.script_tree
        selected_rows = tree.selectionModel().selectedRows(0)
        if len(selected_rows) != 1:
            return False
        file_path = tree.file_model.filePath(selected_rows[0])
        if not tree.is_script_file(file_path):
            return False

        try:
            import nuke

            nuke.nodePaste(file_path)
        except (ImportError, OSError, RuntimeError) as error:
            QtWidgets.QMessageBox.warning(
                self._base_widget.base_widget,
                "Paste Selected failed",
                f"Could not paste the Nuke script:\n{error}",
            )
            return False
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
