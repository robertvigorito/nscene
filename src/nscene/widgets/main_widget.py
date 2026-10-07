"""Core save dialog widget assembled from reusable controls."""

import dataclasses
from Qt import QtWidgets, QtGui, QtCore

from nscene.widgets.script_tree import ExistingScriptsTreeView


@dataclasses.dataclass
class WidgetSettings:
    """Settings for the main widget.

    Attributes:
        project (str): The project name.
        sequence (str): The sequence name.
        shot (str): The shot name.
        description (str): The description of the context.
        version (int): The major version number.
        minor_version (int): The minor version number.
    """

    project: str = ""
    sequence: str = ""
    shot: str = ""
    description: str = ""
    version: int = 1
    minor_version: int = 0

    def as_dict(self):
        """Convert the widget settings to a dictionary."""
        return dataclasses.asdict(self)


class RestrictedLineEdit(QtWidgets.QLineEdit):
    """A QLineEdit with restricted input based on a provided validator."""

    REPLACE_MAPPING = {" ": "_", ".": "_"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.textEdited.connect(self._normalize_user_edit)

    @classmethod
    def normalize_text(cls, text: str) -> str:
        """Convert text to lowercase and replace disallowed path characters."""
        for old, new in cls.REPLACE_MAPPING.items():
            text = text.replace(old, new)
        return text.lower()

    def setText(self, text: str) -> None:
        """Set normalized text, including when called programmatically."""
        super().setText(self.normalize_text(text))

    def _normalize_user_edit(self, text: str) -> None:
        """Normalize typed or pasted text while keeping the cursor position."""
        normalized = self.normalize_text(text)
        if normalized != text:
            cursor_position = self.cursorPosition()
            self.setText(normalized)
            self.setCursorPosition(cursor_position)


class NukeContextDialog(QtWidgets.QDialog):
    """Build the save-as UI without application-specific behavior.

    Attributes:
        project_edit: QtWidgets.QLineEdit
        sequence_edit: QtWidgets.QLineEdit
        shot_edit: QtWidgets.QLineEdit
        description_edit: QtWidgets.QLineEdit
        version_edit: QtWidgets.QSpinBox
        minor_version_edit: QtWidgets.QSpinBox
        preview_panel: QtWidgets.QLineEdit
        script_tree: ExistingScriptsTreeView
        save_button: QtWidgets.QPushButton
        cancel_button: QtWidgets.QPushButton
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.resize(1000, 650)
        self.setMinimumWidth(850)

        self.script_tree = ExistingScriptsTreeView()

        self.form_layout()

    def form_layout(self):
        """Bring all the layouts and the widgets together into the main form layout
        and set it as the main layout of the dialog.

        Returns:
            QtWidgets.QFormLayout: The main form layout containing all sub-layouts and widgets.
        """
        context_layout = self.build_context_layout()

        form_layout = QtWidgets.QFormLayout()
        form_layout.addRow(context_layout)
        description_layout = self.build_description_layout()
        form_layout.addRow(description_layout)

        form_layout.addRow(self.script_tree)

        post_layout = self.build_post_layout()
        form_layout.addRow(post_layout)

        self.setLayout(form_layout)

        return form_layout

    def build_context_layout(self):
        """Build the context layout containing project, sequence, and shot fields.

        Returns:
            QtWidgets.QHBoxLayout: The context layout with project, sequence, and shot widgets.
        """
        self.project_edit: QtWidgets.QLineEdit = QtWidgets.QLineEdit()
        self.project_edit.setPlaceholderText("Project")
        self.sequence_edit: QtWidgets.QLineEdit = QtWidgets.QLineEdit()
        self.sequence_edit.setPlaceholderText("Sequence")

        self.shot_edit: QtWidgets.QLineEdit = QtWidgets.QLineEdit()
        self.shot_edit.setPlaceholderText("Shot")

        context_layout = QtWidgets.QHBoxLayout()
        context_layout.setSpacing(3)
        context_layout.addWidget(self.project_edit)
        context_layout.addWidget(QtWidgets.QLabel("/"))
        context_layout.addWidget(self.sequence_edit)
        context_layout.addWidget(QtWidgets.QLabel("/"))
        context_layout.addWidget(self.shot_edit)
        return context_layout

    def build_description_layout(self):
        """Build the description layout containing the description, version, and minor version fields.

        Returns:
            QtWidgets.QHBoxLayout: The description layout with description, version, and minor version widgets.
        """
        self.description_edit: QtWidgets.QLineEdit = RestrictedLineEdit()
        self.description_edit.setPlaceholderText("Description")

        self.version_edit: QtWidgets.QSpinBox = QtWidgets.QSpinBox()
        self.version_edit.setRange(1, 999999)
        self.version_edit.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)

        self.minor_version_edit: QtWidgets.QSpinBox = QtWidgets.QSpinBox()
        self.minor_version_edit.setRange(0, 999999)
        self.minor_version_edit.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons)

        description_layout = QtWidgets.QHBoxLayout()
        description_layout.setSpacing(1)
        description_layout.addWidget(self.description_edit, 1)
        description_layout.addSpacing(6)
        description_layout.addWidget(self.version_edit)
        dot_label = QtWidgets.QLabel(".")
        description_layout.addWidget(dot_label)
        description_layout.addWidget(self.minor_version_edit)

        return description_layout

    def build_post_layout(self):
        """Build the post layout containing the preview panel and action buttons.

        Returns:
            QtWidgets.QHBoxLayout: The post layout with the preview panel, save button, and cancel button.
        """
        self.preview_panel: QtWidgets.QLineEdit = QtWidgets.QLineEdit()
        self.preview_panel.setReadOnly(True)
        self.preview_panel.setPlaceholderText("The scene save path will appear here")
        self.preview_panel.setStyleSheet("QLineEdit { border: none; background: transparent; padding: 0; }")

        self.save_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Save")
        self.save_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DialogSaveButton))
        self.cancel_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.close)
        self.cancel_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DialogCancelButton))
        icon_size = QtCore.QSize(18, 18)
        self.save_button.setIconSize(icon_size)
        self.cancel_button.setIconSize(icon_size)

        post_layout = QtWidgets.QVBoxLayout()
        post_layout.addWidget(self.preview_panel)
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        post_layout.addSpacing(30)
        post_layout.addLayout(button_layout)

        return post_layout


class FormedNukeContextDialog:
    def __init__(self, parent=None):
        self._base_widget = NukeContextDialog(parent)
        self.settings = QtCore.QSettings("nscene", "save-as")
        self.restore_settings()

        # Shortcut to access the base widget's attributes directly
        QtGui.QShortcut("alt+w", self._base_widget, self._base_widget.close)
        QtGui.QShortcut("alt+up", self._base_widget, lambda: self.version_up_widget(self._base_widget.version_edit))
        QtGui.QShortcut(
            "alt+down", self._base_widget, lambda: self.version_up_widget(self._base_widget.version_edit, step=-1)
        )
        QtGui.QShortcut(
            "alt+shift+up", self._base_widget, lambda: self.version_up_widget(self._base_widget.minor_version_edit)
        )
        QtGui.QShortcut(
            "alt+shift+down",
            self._base_widget,
            lambda: self.version_up_widget(self._base_widget.minor_version_edit, step=-1),
        )
        self._base_widget.show()

        # Save the settings on close and save
        self._base_widget.finished.connect(self.save_settings)
        self._base_widget.accepted.connect(self.save_settings)

    def restore_settings(self) -> None:
        """Restore the previously entered save-form values."""
        defaults = WidgetSettings(
            project=self.settings.value("project", "", type=str),
            sequence=self.settings.value("sequence", "", type=str),
            shot=self.settings.value("shot", "", type=str),
            description=self.settings.value("description", "", type=str),
            version=self.settings.value("version", 1, type=int),
            minor_version=self.settings.value("minor_version", 0, type=int),
        )
        for name, value in defaults.as_dict().items():
            widget = getattr(self._base_widget, f"{name}_edit")
            if isinstance(widget, QtWidgets.QSpinBox):
                widget.setValue(value)
            else:
                widget.setText(value)

    def save_settings(self):
        """Save the current settings to for reuse

        Returns:
            bool: True if the settings were successfully saved.
        """
        widget_settings = self.get_settings()
        for name, value in widget_settings.as_dict().items():
            self.settings.setValue(name, value)
        return True

    def refresh(self): ...

    def get_settings(self):
        """Get the current settings from the base widget.

        Returns:
            WidgetSettings: The current settings of the form.
        """
        return WidgetSettings(
            project=self._base_widget.project_edit.text(),
            sequence=self._base_widget.sequence_edit.text(),
            shot=self._base_widget.shot_edit.text(),
            description=self._base_widget.description_edit.text(),
            version=self._base_widget.version_edit.value(),
            minor_version=self._base_widget.minor_version_edit.value(),
        )

    def get_preview_path(self):
        """Get the preview path from the base widget's preview panel.

        Returns:
            str: The text displayed in the preview panel.
        """
        return self._base_widget.preview_panel.text()

    def version_up_widget(self, widget, step=1):
        """Increment the value of a given widget by a specified step.

        Args:
            widget (QtWidgets.QSpinBox): The widget whose value will be incremented.
            step (int, optional): The amount to increment the widget's value by. Defaults to 1.
        """
        widget.setValue(widget.value() + step)

    def set_preview_path(self, path):
        """Set the preview path in the base widget's preview panel.

        Args:
            path (str): The path to display in the preview panel.
        """
        self._base_widget.preview_panel.setText(path)
