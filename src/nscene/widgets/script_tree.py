"""Filesystem tree widget for previously saved Nuke scripts."""

from PySide6 import QtCore, QtWidgets


class ExistingScriptsTreeView(QtWidgets.QTreeView):
    """Display Nuke scripts in a save directory with filesystem metadata."""

    HEADER_TITLES = ("Script", "Size", "Type", "Modified")

    def __init__(self, parent=None):
        """Initialize the existing scripts tree view."""
        super().__init__(parent)

        self.file_model = QtWidgets.QFileSystemModel(self)
        self.file_model.setFilter(QtCore.QDir.Filter.Files | QtCore.QDir.Filter.NoDotAndDotDot)
        self.file_model.setNameFilters(["*.nk"])
        self.file_model.setNameFilterDisables(False)
        self.setModel(self.file_model)
        self.setRootIsDecorated(False)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSortingEnabled(True)
        self.sortByColumn(3, QtCore.Qt.SortOrder.DescendingOrder)
        self.setMinimumHeight(180)
        header = self.header()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        header.resizeSection(0, 400)
        header.setStretchLastSection(False)
        self.set_headers()
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        # self.customContextMenuRequested.connect(self._show_context_menu)
        self.show()

    def set_headers(self) -> None:
        """Set readable labels for the filesystem metadata columns.

        Returns:
            bool: True if headers were successfully set.
        """
        for column, title in enumerate(self.HEADER_TITLES):
            self.file_model.setHeaderData(column, QtCore.Qt.Orientation.Horizontal, title)

        return True

    def set_save_path(self, save_path: str) -> None:
        """Display scripts beside the target save file, including an empty directory view."""
        directory = QtCore.QFileInfo(save_path).absolutePath()
        self.setRootIndex(self.file_model.setRootPath(directory))
        self.set_headers()
        self.show()

    def clear_directory(self) -> None:
        """Keep the tree visible with an empty root when no target path is available."""
        self.setRootIndex(QtCore.QModelIndex())
        self.show()

    def _show_context_menu(self, position: QtCore.QPoint) -> None:
        """Offer deletion for the selected scripts when a row is right-clicked."""
        index = self.indexAt(position)
        if not index.isValid():
            return

        self.setCurrentIndex(index)
        selection_model = self.selectionModel()
        selected_rows = selection_model.selectedRows(0)
        if not any(row.row() == index.row() for row in selected_rows):
            selection_model.clearSelection()
            file_index = index.siblingAtColumn(0)
            selection_model.select(
                file_index,
                QtCore.QItemSelectionModel.SelectionFlag.ClearAndSelect | QtCore.QItemSelectionModel.SelectionFlag.Rows,
            )
            selected_rows = [file_index]

        file_paths = [self.file_model.filePath(row) for row in selected_rows]

        menu = QtWidgets.QMenu(self)
        delete_action = menu.addAction(f"Delete {len(file_paths)} script(s)")
        if menu.exec(self.viewport().mapToGlobal(position)) != delete_action:
            return

        message = QtWidgets.QMessageBox(self)
        message.setWindowTitle("Delete scripts")
        message.setText(f"Permanently delete {len(file_paths)} selected script(s)?")
        message.setDetailedText("\n".join(QtCore.QFileInfo(path).fileName() for path in file_paths))
        message.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
        message.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)
        answer = message.exec()
        if answer != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        failed_paths = [path for path in file_paths if not QtCore.QFile.remove(path)]
        if failed_paths:
            QtWidgets.QMessageBox.warning(
                self,
                "Some scripts could not be deleted",
                "Could not delete:\n" + "\n".join(failed_paths),
            )
