"""PySide6 dialogs for opening and saving Nuke scenes."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from PySide6 import QtWidgets

from .scene_manager import MongoSceneRepository, NukeAdapter, SceneRecord, SceneRepository


class SceneFields(QtWidgets.QFormLayout):
    def __init__(self, values: dict[str, str] | None = None) -> None:
        super().__init__()
        values = values or {}
        self.project = QtWidgets.QComboBox()
        self.sequence = QtWidgets.QComboBox()
        self.shot = QtWidgets.QComboBox()
        self.scene_type = QtWidgets.QComboBox()
        self.name = QtWidgets.QLineEdit(values.get("name", "scene"))
        for widget, label in (
            (self.project, "Project"), (self.sequence, "Sequence"),
            (self.shot, "Shot"), (self.scene_type, "Type"),
        ):
            widget.setEditable(True)
            self.addRow(label, widget)
        self.addRow("Scene name", self.name)

    def set_choices(self, widget: QtWidgets.QComboBox, values: list[str]) -> None:
        current = widget.currentText()
        widget.clear()
        widget.addItems(values)
        widget.setEditText(current)

    def data(self) -> dict[str, str]:
        return {
            "project": self.project.currentText().strip(),
            "sequence": self.sequence.currentText().strip(),
            "shot": self.shot.currentText().strip(),
            "scene_type": self.scene_type.currentText().strip(),
            "name": self.name.text().strip(),
        }


class SaveAsDialog(QtWidgets.QDialog):
    def __init__(self, repository: SceneRepository, nuke: NukeAdapter) -> None:
        super().__init__()
        self.setWindowTitle("Nuke Save As")
        self.repository, self.nuke = repository, nuke
        form = SceneFields()
        self._form = form
        self.description = QtWidgets.QLineEdit()
        self.version = QtWidgets.QSpinBox()
        self.version.setRange(0, 999)
        self.version.setValue(1)
        self.minor = QtWidgets.QSpinBox()
        self.minor.setRange(0, 99)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(form)
        form.addRow("Description", self.description)
        form.addRow("Version (v###)", self.version)
        form.addRow("Minor (##)", self.minor)
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def save(self) -> None:
        try:
            data = self._form.data()
            path = self.repository.save_path(
                **data, version=self.version.value(), minor=self.minor.value(),
                description=self.description.text(),
            )
            self.nuke.save_as(path)
            self.repository.record_scene(
                data["project"], data["sequence"], data["shot"], data["scene_type"], path
            )
        except (OSError, ValueError, RuntimeError) as exc:
            QtWidgets.QMessageBox.warning(self, "Unable to save scene", str(exc))
            return
        self.accept()


class OpenDialog(QtWidgets.QDialog):
    HEADERS = ("Name", "Version", "Date created", "Date modified")

    def __init__(self, repository: SceneRepository, nuke: NukeAdapter) -> None:
        super().__init__()
        self.setWindowTitle("Nuke Open Scene")
        self.repository, self.nuke = repository, nuke
        self.records: list[SceneRecord] = []
        self._form = SceneFields()
        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(self._form)
        self.table = QtWidgets.QTableWidget(0, len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.table.doubleClicked.connect(lambda _: self.open_scene())
        layout.addWidget(self.table)
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Open | QtWidgets.QDialogButtonBox.Cancel
        )
        copy_button = buttons.addButton("Copy to group", QtWidgets.QDialogButtonBox.ActionRole)
        buttons.accepted.connect(self.open_scene)
        buttons.rejected.connect(self.reject)
        copy_button.clicked.connect(self.copy_scene)
        self._form.project.editTextChanged.connect(self.refresh)
        self._form.sequence.editTextChanged.connect(self.refresh)
        self._form.shot.editTextChanged.connect(self.refresh)
        self._form.scene_type.editTextChanged.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        data = self._form.data()
        self.records = self.repository.list_scenes(
            data["project"], data["sequence"], data["shot"], data["scene_type"]
        )
        self.table.setRowCount(len(self.records))
        for row, record in enumerate(self.records):
            values = (record.name, record.version_label,
                      record.created.strftime("%Y-%m-%d %H:%M"),
                      record.modified.strftime("%Y-%m-%d %H:%M"))
            for column, value in enumerate(values):
                self.table.setItem(row, column, QtWidgets.QTableWidgetItem(value))
        self.table.resizeColumnsToContents()

    def _selected(self) -> SceneRecord | None:
        row = self.table.currentRow()
        return self.records[row] if 0 <= row < len(self.records) else None

    def _run(self, action: Callable[[Path], None]) -> None:
        record = self._selected()
        if record is None:
            QtWidgets.QMessageBox.information(self, "Select a scene", "Select a saved scene first.")
            return
        try:
            action(record.path)
        except (OSError, RuntimeError) as exc:
            QtWidgets.QMessageBox.warning(self, "Unable to open scene", str(exc))
            return
        self.accept()

    def open_scene(self) -> None:
        self._run(self.nuke.open)

    def copy_scene(self) -> None:
        self._run(self.nuke.copy_to_group)


def _repository(root: str | Path, mongo_uri: str | None) -> SceneRepository:
    if mongo_uri:
        return MongoSceneRepository(root, mongo_uri)
    return SceneRepository(root)


def show_save_as(
    root: str | Path, parent: QtWidgets.QWidget | None = None, mongo_uri: str | None = None
) -> int:
    return SaveAsDialog(_repository(root, mongo_uri), NukeAdapter()).exec()


def show_open(
    root: str | Path, parent: QtWidgets.QWidget | None = None, mongo_uri: str | None = None
) -> int:
    return OpenDialog(_repository(root, mongo_uri), NukeAdapter()).exec()
