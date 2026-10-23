"""Open existing Nuke scripts using the shared save-form widgets."""

import sys
from datetime import date

from Qt import QtCore, QtGui, QtWidgets

from nscene.paths import current_package_root, get_projects_root
from nscene.widgets.main_widget import FormedNukeContextDialog
from nscene.widgets.script_tree import ExistingScriptsTreeView


class _ScriptDropFilter(QtCore.QObject):
    """Accept dropped Nuke script files and forward them to the Open interface."""

    def __init__(self, owner, parent=None):
        super().__init__(parent)
        self.owner = owner

    @staticmethod
    def _script_paths(event) -> list[str]:
        """Return local .nk files carried by a drag/drop event."""
        mime_data = event.mimeData()
        if not mime_data.hasUrls():
            return []
        return [
            url.toLocalFile()
            for url in mime_data.urls()
            if url.isLocalFile() and ExistingScriptsTreeView.is_script_file(url.toLocalFile())
        ]

    def eventFilter(self, watched, event):
        """Handle drag-enter, drag-move, and drop events for Nuke scripts."""
        event_type = event.type()
        if event_type in (QtCore.QEvent.Type.DragEnter, QtCore.QEvent.Type.DragMove):
            if self._script_paths(event):
                event.acceptProposedAction()
                return True
        elif event_type == QtCore.QEvent.Type.Drop:
            script_paths = self._script_paths(event)
            if script_paths:
                event.acceptProposedAction()
                self.owner.open_script(script_paths[0])
                return True
        return super().eventFilter(watched, event)


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
        self._base_widget.clear_script_button.hide()

        self._base_widget.set_context_fields_visible(True)
        self._base_widget.set_save_fields_visible(False)
        self._base_widget.script_tree.file_model.setFilter(
            QtCore.QDir.Filter.AllDirs | QtCore.QDir.Filter.Files | QtCore.QDir.Filter.NoDotAndDotDot
        )
        self._base_widget.script_tree.setRootIsDecorated(True)
        self._drop_filter = _ScriptDropFilter(self, self._base_widget)
        drop_targets = [self._base_widget, *self._base_widget.findChildren(QtWidgets.QWidget)]
        for drop_target in drop_targets:
            drop_target.setAcceptDrops(True)
            drop_target.installEventFilter(self._drop_filter)
        for context_edit in (
            self._base_widget.project_edit,
            self._base_widget.sequence_edit,
            self._base_widget.shot_edit,
        ):
            context_edit.textChanged.connect(self._refresh_script_directory)
        self._base_widget.script_tree.clicked.connect(self._select_script)
        self._base_widget.script_tree.doubleClicked.connect(self.open_selected_script)
        self._base_widget.script_tree.customContextMenuRequested.connect(self._show_script_context_menu)
        self._base_widget.save_button.clicked.connect(lambda _checked=False: self.open_selected_script())
        self._base_widget.paste_selected_action.triggered.connect(lambda _checked=False: self.paste_selected_script())
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
            if all(context):
                directory = QtCore.QDir(directory).filePath("nuke")
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
        if file_info.isFile() and ExistingScriptsTreeView.is_script_file(file_path):
            return file_path
        return ""

    def _select_script(self, index) -> None:
        """Display the selected script path in the preview field."""
        file_path = self._selected_script_path(index)
        self._base_widget.preview_panel.setText(file_path)
        self._base_widget.save_button.setEnabled(bool(file_path))

    def _show_script_context_menu(self, position: QtCore.QPoint) -> None:
        """Show script actions and common path utilities for the clicked tree row."""
        tree = self._base_widget.script_tree
        index = tree.indexAt(position)
        if not index.isValid():
            return

        tree.setCurrentIndex(index)
        selection_model = tree.selectionModel()
        if not any(row.row() == index.row() for row in selection_model.selectedRows(0)):
            selection_model.clearSelection()
            selection_model.select(
                index.siblingAtColumn(0),
                QtCore.QItemSelectionModel.SelectionFlag.ClearAndSelect | QtCore.QItemSelectionModel.SelectionFlag.Rows,
            )

        selected_paths = [tree.file_model.filePath(row) for row in selection_model.selectedRows(0)]
        script_paths = [path for path in selected_paths if ExistingScriptsTreeView.is_script_file(path)]
        menu = QtWidgets.QMenu(tree)
        open_action = menu.addAction("Open")
        insert_action = menu.addAction("Insert as Drop")
        insert_group_action = menu.addAction("Insert as Drop Group")
        set_root_action = menu.addAction("Set Browser Root Here")
        set_script_name_action = menu.addAction("Set Root Name to Path")
        menu.addSeparator()
        copy_path_action = menu.addAction("Copy Path")
        copy_name_action = menu.addAction("Copy File Name")
        copy_folder_action = menu.addAction("Copy Folder Path")
        menu.addSeparator()
        show_folder_action = menu.addAction("Open Containing Folder")
        open_action.setEnabled(len(script_paths) == 1)
        insert_action.setEnabled(len(script_paths) == 1)
        insert_group_action.setEnabled(len(script_paths) == 1)
        set_root_action.setEnabled(len(script_paths) == 1)
        set_script_name_action.setEnabled(len(script_paths) == 1)

        chosen_action = menu.exec(tree.viewport().mapToGlobal(position))
        if chosen_action == open_action:
            self.open_script(script_paths[0])
        elif chosen_action == insert_action:
            self.insert_script_as_drop(script_paths[0])
        elif chosen_action == insert_group_action:
            self.insert_script_as_drop(script_paths[0], into_group=True)
        elif chosen_action == set_root_action:
            self.set_script_directory_root(script_paths[0])
        elif chosen_action == set_script_name_action:
            self.set_nuke_root_name(script_paths[0])
        elif chosen_action == copy_path_action:
            QtWidgets.QApplication.clipboard().setText("\n".join(selected_paths))
        elif chosen_action == copy_name_action:
            names = [QtCore.QFileInfo(path).fileName() for path in selected_paths]
            QtWidgets.QApplication.clipboard().setText("\n".join(names))
        elif chosen_action == copy_folder_action:
            folders = [QtCore.QFileInfo(path).absolutePath() for path in selected_paths]
            QtWidgets.QApplication.clipboard().setText("\n".join(folders))
        elif chosen_action == show_folder_action and selected_paths:
            folder = QtCore.QFileInfo(selected_paths[0]).absolutePath()
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(folder))

    def set_script_directory_root(self, file_path: str) -> bool:
        """Set the file tree root to the selected script's containing directory.

        Args:
            file_path: Path to a Nuke script in the tree.

        Returns:
            True when the browser root was updated, otherwise False.
        """
        file_info = QtCore.QFileInfo(file_path)
        if not file_info.isFile() or not ExistingScriptsTreeView.is_script_file(file_path):
            return False

        directory = file_info.absolutePath()
        if not QtCore.QDir(directory).exists():
            return False

        self._base_widget.script_tree.set_directory(directory)
        self._base_widget.preview_panel.setText(file_info.absoluteFilePath())
        self._base_widget.save_button.setEnabled(True)
        return True

    def set_nuke_root_name(self, file_path: str) -> bool:
        """Set the Nuke root node's script name to the selected file path.

        Args:
            file_path: Path to a Nuke script in the tree.

        Returns:
            True when the root node name was updated, otherwise False.
        """
        file_info = QtCore.QFileInfo(file_path)
        if not file_info.isFile() or not ExistingScriptsTreeView.is_script_file(file_path):
            return False

        import nuke

        try:
            nuke.root()["name"].setValue(file_info.absoluteFilePath())
        except (OSError, RuntimeError, ValueError) as error:
            QtWidgets.QMessageBox.warning(
                self._base_widget,
                "Set Nuke Root Name failed",
                f"Could not set the Nuke root name:\n{error}",
            )
            return False
        return True

    def open_selected_script(self, index=None) -> bool:
        """Open the selected script in Nuke and close the dialog."""
        file_path = self._selected_script_path(index)
        if not file_path:
            return False

        return self.open_script(file_path)

    def open_script(self, file_path: str) -> bool:
        """Open a Nuke script in Nuke."""
        if not ExistingScriptsTreeView.is_script_file(file_path):
            return False

        import nuke

        try:
            nuke.scriptOpen(file_path)
        except (OSError, RuntimeError) as error:
            QtWidgets.QMessageBox.warning(
                self._base_widget,
                "Open failed",
                f"Could not open the Nuke script:\n{error}",
            )
            return False
        context = (
            self._base_widget.project_edit.text(),
            self._base_widget.sequence_edit.text(),
            self._base_widget.shot_edit.text(),
        )
        if any(context):
            self._form.record_context(context)
        else:
            self._form.record_script_context(file_path)
        self._base_widget.accept()
        return True

    def paste_selected_script(self) -> bool:
        """Paste the selected script's nodes into the current Nuke node graph."""
        file_path = self._selected_script_path()
        if not file_path:
            return False
        return self.insert_script_as_drop(file_path)

    def insert_script_as_drop(self, file_path: str, *, into_group: bool = False) -> bool:
        """Paste script nodes into the graph and optionally collapse them into a new Group.

        Args:
            file_path: Path to the Nuke script to insert.
            into_group: Collapse the pasted nodes into a new Group and label it with the file name and date.

        Returns:
            True when the script was inserted successfully, otherwise False.
        """
        if not ExistingScriptsTreeView.is_script_file(file_path):
            return False

        import nuke

        try:
            nuke.nodePaste(file_path)
            if into_group:
                group = nuke.collapseToGroup()
                script_base_name = QtCore.QFileInfo(file_path).completeBaseName()
                group["label"].setValue(f"{script_base_name}\n{date.today():%Y-%m-%d}")
        except (OSError, RuntimeError) as error:
            QtWidgets.QMessageBox.warning(
                self._base_widget,
                "Insert as Drop failed",
                f"Could not insert the Nuke script:\n{error}",
            )
            return False

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
