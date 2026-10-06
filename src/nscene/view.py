"""Build a Nuke save and open interface."""

from PySide6 import QtCore, QtWidgets

from necessities import assemble


class NSaveView(QtWidgets.QDialog):
    """Nuke save/open dialog view.

    Attributes:
        scene_assembler(assemble.Scene): The scene assembler instance.
    """

    def __init__(self, parent=None):
        """Initialize the Nuke save/open dialog view.

            Args:
        parent: The parent widget.
        """

        super().__init__(parent)

        self.scene_assembler = assemble.Scene.from_application("nuke", root="/vfx/wgid/projects")
        self.settings = QtCore.QSettings("nscene", "save-as")

        self.project_edit = QtWidgets.QLineEdit()
        self.project_edit.setPlaceholderText("Project")

        self.sequence_edit = QtWidgets.QLineEdit()
        self.sequence_edit.setPlaceholderText("Sequence")

        self.shot_edit = QtWidgets.QLineEdit()
        self.shot_edit.setPlaceholderText("Shot")

        # description layout
        self.description_edit = QtWidgets.QLineEdit()
        self.description_edit.setPlaceholderText("Description")

        # Version layout
        self.version_edit = QtWidgets.QLineEdit()
        self.version_edit.setPlaceholderText("Supports versioning with 001, 002 or v001.01")
        self.version_edit.installEventFilter(self)

        # Preview panel
        self.preview_panel = QtWidgets.QLineEdit()
        self.preview_panel.setReadOnly(True)
        self.preview_panel.setPlaceholderText("The scene save path will appear here")

        self.script_model = QtWidgets.QFileSystemModel(self)
        self.script_model.setFilter(QtCore.QDir.Filter.Files | QtCore.QDir.Filter.NoDotAndDotDot)
        self.script_model.setNameFilters(["*.nk"])
        self.script_model.setNameFilterDisables(False)

        self.script_tree = QtWidgets.QTreeView()
        self.script_tree.setModel(self.script_model)
        self.script_tree.setRootIsDecorated(False)
        self.script_tree.setSortingEnabled(True)
        self.script_tree.sortByColumn(3, QtCore.Qt.SortOrder.DescendingOrder)
        self.script_tree.setMinimumHeight(180)

        for name, widget in (
            ("project", self.project_edit),
            ("sequence", self.sequence_edit),
            ("shot", self.shot_edit),
            ("description", self.description_edit),
            ("version", self.version_edit),
        ):
            value = self.settings.value(name, "", str)
            if name != "version":
                value = self.normalize_text(value)
            widget.setText(value)

        # Save layout
        self.save_button = QtWidgets.QPushButton("Save")
        self.save_button.clicked.connect(self.save)

        # Cancel Button
        self.cancel_button = QtWidgets.QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.close)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)

        context_layout = QtWidgets.QHBoxLayout()
        context_layout.addWidget(self.project_edit)
        context_layout.addWidget(QtWidgets.QLabel("/"))
        context_layout.addWidget(self.sequence_edit)
        context_layout.addWidget(QtWidgets.QLabel("/"))
        context_layout.addWidget(self.shot_edit)

        layout = QtWidgets.QFormLayout(self)
        layout.addRow("Context", context_layout)
        layout.addRow("Description", self.description_edit)
        layout.addRow("Version", self.version_edit)
        layout.addRow("Save path", self.preview_panel)
        layout.addRow("Existing scripts", self.script_tree)

        layout.addRow(button_layout)

        self.setLayout(layout)

        for m in (
            self.project_edit,
            self.sequence_edit,
            self.shot_edit,
            self.description_edit,
            self.version_edit,
        ):
            m.textChanged.connect(self.form_path)
            m.textChanged.connect(self.save_settings)
        for m in (self.project_edit, self.sequence_edit, self.shot_edit, self.description_edit):
            m.textEdited.connect(self.normalize_text_edit)
        self.form_path()

    @staticmethod
    def normalize_text(value):
        """Convert path text to lowercase underscore-separated text."""
        return value.replace(" ", "_").lower()

    def normalize_text_edit(self, _text=""):
        """Normalize the line edit currently being edited."""
        widget = self.sender()
        if not isinstance(widget, QtWidgets.QLineEdit):
            return
        cursor_position = widget.cursorPosition()
        normalized = self.normalize_text(widget.text())
        if normalized != widget.text():
            widget.setText(normalized)
            widget.setCursorPosition(cursor_position)

    def save_settings(self, _text=""):
        """Persist the last values entered in the save form."""
        for name, widget in (
            ("project", self.project_edit),
            ("sequence", self.sequence_edit),
            ("shot", self.shot_edit),
            ("description", self.description_edit),
            ("version", self.version_edit),
        ):
            self.settings.setValue(name, widget.text())

    def eventFilter(self, watched, event):
        """Handle version changes from the Up and Down arrow keys."""
        if watched is self.version_edit and event.type() == QtCore.QEvent.Type.KeyPress:
            if event.key() == QtCore.Qt.Key.Key_Up:
                self.change_version(1)
                return True
            if event.key() == QtCore.Qt.Key.Key_Down:
                self.change_version(-1)
                return True
        return super().eventFilter(watched, event)

    def change_version(self, amount):
        """Increment or decrement the major version while preserving formatting."""
        version_text = self.version_edit.text().strip()
        version_part, separator, minor_part = version_text.partition(".")
        prefix = "v" if version_part.lower().startswith("v") else ""
        digits = version_part[len(prefix) :] or "0"
        try:
            version = max(0, int(digits) + amount)
        except ValueError:
            return False

        version_value = f"{version:0{len(digits)}d}"
        new_text = f"{prefix}{version_value}"
        if separator:
            new_text += f".{minor_part}"
        self.version_edit.setText(new_text)
        return True

    def form_path(self):
        """Form the path from the UI elements.

        Returns:
            bool: True if successful.
        """
        context = (
            self.normalize_text(self.project_edit.text()),
            self.normalize_text(self.sequence_edit.text()),
            self.normalize_text(self.shot_edit.text()),
        )
        for key, value in zip(("show", "sequence", "shot"), context):
            setattr(self.scene_assembler, key, value)

        version = version_minor = 0
        self.scene_assembler.description = self.normalize_text(self.description_edit.text())

        # Check if the version is in 1.1 format
        version_text = self.version_edit.text()
        try:
            if "." in version_text:
                version_part, minor_part = version_text.split(".", 1)
                version = int(version_part.replace("v", ""))
                version_minor = int(minor_part)
            else:
                version = int(version_text.replace("v", "") or 1)
                version_minor = 0
        except ValueError:
            self.preview_panel.clear()
            return False

        self.scene_assembler.version = version
        self.scene_assembler.minor_version = version_minor
        if any(context):
            resolved_path = self.scene_assembler.resolve()
            self.preview_panel.setText(resolved_path)
            self.refresh_script_tree(resolved_path)
        else:
            self.preview_panel.clear()
            self.script_tree.setVisible(False)
        return True

    def refresh_script_tree(self, resolved_path):
        """Show existing Nuke scripts from the resolved script directory."""
        directory = QtCore.QFileInfo(resolved_path).absolutePath()
        if not QtCore.QDir(directory).exists():
            self.script_tree.setVisible(False)
            return

        root_index = self.script_model.setRootPath(directory)
        self.script_tree.setRootIndex(root_index)
        for column, title in enumerate(("Script", "Size", "Type", "Modified")):
            self.script_model.setHeaderData(column, QtCore.Qt.Orientation.Horizontal, title)
        self.script_tree.setVisible(True)

    def save(self):
        """Save the current scene.

        Returns:
            bool: True if successful.
        """
        # Here you would add the Nuke specific save code
        self.close()

        return True


def load():
    """Load and return the Nuke save/open view."""
    import sys

    app = QtWidgets.QApplication(sys.argv)

    view = NSaveView()
    view.show()
    app.exec()
    return view


def load_in_application():
    """Load the Nuke save/open view in an existing application.

    Returns:
        Optional[NSaveView]: The Nuke save/open view.
    """
    view = NSaveView()
    view.show()
    print("Loaded NSaveView in existing application.")
    return view


load()
