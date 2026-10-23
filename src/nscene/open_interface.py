"""Open existing Nuke scripts using the shared save-form widgets."""

import sys

from Qt import QtCore, QtWidgets

from nscene.paths import current_package_root, get_projects_root
from nscene.widgets.main_widget import FormedNukeContextDialog


class NukeOpenInterface:
    """Control an open-scene dialog built from the shared context widgets."""

    def __init__(self, parent=None):
        self._form = FormedNukeContextDialog(parent, projects_root=get_projects_root(), show=False)
        self._base_widget = self._form.base_widget
        self._base_widget.setWindowTitle("Open Nuke Scene")
        self._base_widget.preview_panel.setPlaceholderText("Select a scene to open")
        self._base_widget.save_button.setText("Open")
        self._base_widget.save_button.setIcon(
            self._base_widget.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DialogOpenButton)
        )

        self._base_widget.set_context_fields_visible(True)
        self._base_widget.set_save_fields_visible(False)
        self._base_widget.script_tree.file_model.setFilter(
            QtCore.QDir.Filter.AllDirs | QtCore.QDir.Filter.Files | QtCore.QDir.Filter.NoDotAndDotDot
        )
        self._base_widget.script_tree.setRootIsDecorated(True)
        for context_edit in (
            self._base_widget.project_edit,
            self._base_widget.sequence_edit,
            self._base_widget.shot_edit,
        ):
            context_edit.textChanged.connect(self._refresh_script_directory)
        self._base_widget.script_tree.clicked.connect(self._select_script)
        self._base_widget.script_tree.doubleClicked.connect(self.open_selected_script)
        self._base_widget.save_button.clicked.connect(lambda _checked=False: self.open_selected_script())
        self._base_widget.save_button.setEnabled(False)
        self._refresh_script_directory()
        self._base_widget.show()

    def _refresh_script_directory(self, *_args: object) -> bool:
        """Navigate the file tree to the directory matching the entered context.

        Args:
            *_args: Text-change signal arguments, which are unused.

        Returns:
            True after the tree and selection controls are refreshed.
        """
        context = (
            self._base_widget.project_edit.text(),
            self._base_widget.sequence_edit.text(),
            self._base_widget.shot_edit.text(),
        )
        if any(context):
            directory = self._form.projects_root
            for part in context:
                if not part:
                    break
                directory = QtCore.QDir(directory).filePath(part)
        else:
            directory = current_package_root(self._form.projects_root)

        if QtCore.QDir(directory).exists():
            self._base_widget.script_tree.set_directory(directory)
        else:
            self._base_widget.script_tree.clear_directory()
        self._base_widget.preview_panel.clear()
        self._base_widget.save_button.setEnabled(False)
        return True

    def _selected_script_path(self, index=None) -> str:
        """Return the selected Nuke script path from the filesystem widget."""
        tree = self._base_widget.script_tree
        if index is None or not index.isValid():
            selected_rows = tree.selectionModel().selectedRows(0)
            index = selected_rows[0] if selected_rows else tree.currentIndex()
        if not index.isValid():
            return ""

        file_path = tree.file_model.filePath(index.siblingAtColumn(0))
        file_info = QtCore.QFileInfo(file_path)
        if file_info.isFile() and file_info.suffix().lower() == "nk":
            return file_path
        return ""

    def _select_script(self, index) -> None:
        """Display the selected script path in the preview field."""
        file_path = self._selected_script_path(index)
        self._base_widget.preview_panel.setText(file_path)
        self._base_widget.save_button.setEnabled(bool(file_path))

    def open_selected_script(self, index=None) -> bool:
        """Open the selected script in Nuke and close the dialog."""
        file_path = self._selected_script_path(index)
        if not file_path:
            return False

        import nuke

        nuke.scriptOpen(file_path)
        self._base_widget.accept()
        return True

    def show(self) -> None:
        """Show the open-scene dialog."""
        self._base_widget.show()

    def close(self) -> None:
        """Close the open-scene dialog."""
        self._form.close()


def load():
    """Create and run the interface in a standalone Qt application."""
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    view = NukeOpenInterface()
    app.exec()
    return view


def load_in_application():
    """Show the interface in an existing Nuke application."""
    view = NukeOpenInterface()
    return view
