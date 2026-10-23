"""Core save dialog widget assembled from reusable controls."""

import dataclasses
import json

from necessities import assemble
from Qt import QtCore, QtGui, QtWidgets

from nscene.paths import get_projects_root
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
        show_autosaves_checkbox: QtWidgets.QCheckBox
        save_button: QtWidgets.QPushButton
        clear_script_button: QtWidgets.QPushButton
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
        self.menu_bar = QtWidgets.QMenuBar(self)
        self.history_menu = self.menu_bar.addMenu("History")
        self.options_menu = self.menu_bar.addMenu("Options")
        self.show_autosaves_action = self.options_menu.addAction("Show Autosave Files")
        self.show_autosaves_action.setCheckable(True)
        self.paste_selected_action = self.options_menu.addAction("Paste Selected")
        self.paste_selected_action.setEnabled(False)
        form_layout.addRow(self.menu_bar)
        form_layout.addRow(context_layout)
        description_layout = self.build_description_layout()
        self.description_container = QtWidgets.QWidget(self)
        self.description_container.setLayout(description_layout)
        form_layout.addRow(self.description_container)

        self.show_autosaves_checkbox = QtWidgets.QCheckBox("Show Autosave Files")
        self.show_autosaves_checkbox.toggled.connect(self.script_tree.set_show_autosaves)
        form_layout.addRow(self.show_autosaves_checkbox)

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
        self.context_separator_one = QtWidgets.QLabel("/")
        context_layout.addWidget(self.context_separator_one)
        context_layout.addWidget(self.sequence_edit)
        self.context_separator_two = QtWidgets.QLabel("/")
        context_layout.addWidget(self.context_separator_two)
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
        self.clear_script_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Clear Script + Save As")
        self.clear_script_button.setToolTip("Clear the current Nuke script, then save an empty script to this path.")
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
        button_layout.addWidget(self.clear_script_button)
        button_layout.addWidget(self.cancel_button)
        post_layout.addSpacing(30)
        post_layout.addLayout(button_layout)

        return post_layout

    def set_context_fields_visible(self, visible: bool) -> None:
        """Show or hide project, sequence, and shot fields, leaving history available."""
        for widget in (
            self.project_edit,
            self.sequence_edit,
            self.shot_edit,
            self.context_separator_one,
            self.context_separator_two,
        ):
            widget.setVisible(visible)

    def set_save_fields_visible(self, visible: bool) -> None:
        """Show or hide description and version controls used only when saving."""
        self.description_container.setVisible(visible)


class FormedNukeContextDialog:
    HISTORY_LIMIT = 20

    def __init__(self, parent=None, projects_root=None, show=True):
        self._base_widget = NukeContextDialog(parent)
        self.settings = QtCore.QSettings("nscene", "save-as")
        self.projects_root = projects_root or get_projects_root()
        self.restore_settings()
        show_autosaves = self.settings.value("show_autosaves", False, type=bool)
        self._base_widget.show_autosaves_action.setChecked(show_autosaves)
        self._base_widget.script_tree.set_show_autosaves(show_autosaves)
        self._base_widget.show_autosaves_action.toggled.connect(self._set_show_autosaves)
        self._base_widget.script_tree.selectionModel().selectionChanged.connect(self._update_paste_action)
        self._update_paste_action()
        self._install_completers()
        self._refresh_history_menu()

        for field, widget in (
            ("project", self._base_widget.project_edit),
            ("sequence", self._base_widget.sequence_edit),
            ("shot", self._base_widget.shot_edit),
        ):
            widget.textChanged.connect(lambda _text, changed=field: self._context_changed(changed))

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
        if show:
            self._base_widget.show()

        # Save the settings on close and save
        self._base_widget.finished.connect(self.save_settings)
        self._base_widget.accepted.connect(self.save_settings)

    @property
    def base_widget(self) -> NukeContextDialog:
        """Return the reusable Qt dialog managed by this controller."""
        return self._base_widget

    def show(self) -> None:
        """Show the managed dialog."""
        self._base_widget.show()

    def close(self) -> None:
        """Close the managed dialog."""
        self._base_widget.close()

    def _set_show_autosaves(self, visible: bool) -> None:
        """Update autosave visibility and persist the option."""
        self._base_widget.script_tree.set_show_autosaves(visible)
        self.settings.setValue("show_autosaves", visible)
        self._update_paste_action()

    def _update_paste_action(self, *_args: object) -> None:
        """Enable Paste Selected when exactly one Nuke script is selected."""
        selected_rows = self._base_widget.script_tree.selectionModel().selectedRows(0)
        selected_scripts = [
            row
            for row in selected_rows
            if self._base_widget.script_tree.file_model.fileInfo(row).isFile()
            and ExistingScriptsTreeView.is_script_file(self._base_widget.script_tree.file_model.filePath(row))
        ]
        self._base_widget.paste_selected_action.setEnabled(len(selected_scripts) == 1)

    @staticmethod
    def _directory_names(path: str) -> list[str]:
        """List visible child directories at a path, returning an empty list if unavailable."""
        directory = QtCore.QDir(path)
        if not directory.exists():
            return []
        return directory.entryList(
            filters=QtCore.QDir.Filter.Dirs | QtCore.QDir.Filter.NoDotAndDotDot,
            sort=QtCore.QDir.SortFlag.Name,
        )

    def _install_completers(self) -> None:
        """Attach popup completions sourced from the matching directory level on disk."""
        widget = self._base_widget
        self._completers = {}
        for key, line_edit in (
            ("project", widget.project_edit),
            ("sequence", widget.sequence_edit),
            ("shot", widget.shot_edit),
        ):
            completer = QtWidgets.QCompleter(line_edit)
            completer.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)
            completer.setCompletionMode(QtWidgets.QCompleter.CompletionMode.PopupCompletion)
            line_edit.setCompleter(completer)
            self._completers[key] = completer
        self._refresh_completions()

    def _refresh_completions(self, *keys: str) -> None:
        """Refresh completion lists from their matching parent directories."""
        widget = self._base_widget
        scene = assemble.Scene.from_application(
            "nuke",
            root=self.projects_root,
            show=widget.project_edit.text(),
            sequence=widget.sequence_edit.text(),
            shot=widget.shot_edit.text(),
        )
        show_directory = QtCore.QDir(scene.root).filePath(scene.show) if scene.show else scene.root
        sequence_directory = QtCore.QDir(show_directory).filePath(scene.sequence) if scene.sequence else show_directory
        completion_sources = {
            "project": scene.root,
            "sequence": show_directory,
            "shot": sequence_directory,
        }
        for key in keys or tuple(completion_sources):
            source_path = completion_sources[key]
            self._completers[key].setModel(
                QtCore.QStringListModel(self._directory_names(source_path), self._completers[key])
            )

    def _context_changed(self, field: str) -> None:
        """Refresh disk suggestions and persist complete contexts that exist on disk."""
        if field == "project":
            self._refresh_completions("sequence", "shot")
        elif field == "sequence":
            self._refresh_completions("shot")
        self.save_settings()

    def _read_history(self) -> list[tuple[str, str, str]]:
        """Read recent project/sequence/shot contexts from settings."""
        try:
            values = json.loads(self.settings.value("context_history", "[]", type=str))
        except (TypeError, ValueError):
            return []
        return [tuple(item) for item in values if isinstance(item, list) and len(item) == 3]

    def _refresh_history_menu(self) -> None:
        """Rebuild the menu of recently used contexts."""
        menu = self._base_widget.history_menu
        menu.clear()
        history = self._read_history()
        if not history:
            action = menu.addAction("No recent contexts")
            action.setEnabled(False)
            return
        for context in history:
            action = menu.addAction(" / ".join(context))
            action.setData(context)
            action.triggered.connect(lambda _checked=False, selected=context: self._apply_history(selected))

    def _record_context(self, settings: WidgetSettings) -> None:
        """Remember a context only when the corresponding directory exists on disk."""
        context = (settings.project, settings.sequence, settings.shot)
        if not all(context):
            return
        context_path = QtCore.QDir(self.projects_root).filePath(context[0])
        context_path = QtCore.QDir(context_path).filePath(context[1])
        context_path = QtCore.QDir(context_path).filePath(context[2])
        if not QtCore.QDir(context_path).exists():
            return
        history = [entry for entry in self._read_history() if entry != context]
        history.insert(0, context)
        self.settings.setValue(
            "context_history",
            json.dumps(history[: self.HISTORY_LIMIT]),
        )
        self._refresh_history_menu()

    def _apply_history(self, context: tuple[str, str, str]) -> None:
        """Navigate to a context selected from history."""
        line_edits = (
            self._base_widget.project_edit,
            self._base_widget.sequence_edit,
            self._base_widget.shot_edit,
        )
        blockers = [QtCore.QSignalBlocker(line_edit) for line_edit in line_edits]
        for line_edit, value in zip(line_edits, context):
            line_edit.setText(value)
        del blockers
        self._refresh_completions()
        self.save_settings()

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
        self._record_context(widget_settings)
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
