"""Build a Nuke save and open interface."""

from Qt import QtWidgets

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

        self.scene_assembler = assemble.Scene.from_application("nuke")

        self.project_level_edit = QtWidgets.QLineEdit()
        self.project_level_edit.setPlaceholderText("Project Level, show, sequence and shot seperated by .")

        # description layout
        self.description_edit = QtWidgets.QLineEdit()
        self.description_edit.setPlaceholderText("Description")

        # Version layout
        self.version_edit = QtWidgets.QLineEdit()
        self.version_edit.setPlaceholderText("Supports versioning with 001, 002 or v001.01")

        # Preview panel
        self.preview_panel = QtWidgets.QLabel()
        self.preview_panel.setContentsMargins(0, 0, 0, 0)
        # self.preview_panel.setStyleSheet("border-right: 10px double ; margin: 0;")

        # Save layout
        self.save_button = QtWidgets.QPushButton("Save")
        self.save_button.clicked.connect(self.save)

        # Cancel Button
        self.cancel_button = QtWidgets.QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.close)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)

        layout = QtWidgets.QFormLayout(self)
        layout.addRow("Context", self.project_level_edit)
        layout.addRow("Description", self.description_edit)
        layout.addRow("Version", self.version_edit)
        layout.addRow(None, self.preview_panel)

        layout.addRow(button_layout)

        self.setLayout(layout)

        for m in (self.project_level_edit, self.description_edit, self.version_edit):
            m.textChanged.connect(self.form_path)

    def form_path(self):
        """Form the path from the UI elements.

        Returns:
            bool: True if successful.
        """
        context = self.project_level_edit.text().split(".")
        for key, value in zip(["project", "sequence", "shot"], context):
            setattr(self.scene_assembler, key, value)

        version = version_minor = 0
        self.scene_assembler.description = self.description_edit.text()

        # Check if the version is in 1.1 format
        version_text = self.version_edit.text()
        if "." in version_text:
            version_part, minor_part = version_text.split(".", 1)
            version = int(version_part.replace("v", ""))
            version_minor = int(minor_part)
        else:
            version = int(version_text.replace("v", "") or 1)
            version_minor = 0

        self.scene_assembler.version = version
        self.scene_assembler.minor_version = version_minor
        if self.description_edit.text() and self.project_level_edit.text():
            resolved_path = self.scene_assembler.resolve()
            self.preview_panel.setText(resolved_path)
        return True

    def save(self):
        """Save the current scene.

        Returns:
            bool: True if successful.
        """
        resolved_path = self.scene_assembler.resolve()
        # Here you would add the Nuke specific save code
        self.close()

        return True


def load():
    """Load and return the Nuke save/open view."""
    import sys

    app = QtWidgets.QApplication(sys.argv)

    view = NSaveView()
    view.show()
    app.exec_()
    return view


def load_in_application():
    """Load the Nuke save/open view in an existing application.

    Returns:
        Optional[NSaveView]: The Nuke save/open view.
    """
    view = NSaveView()
    view.show()
    return view


load_in_application()
