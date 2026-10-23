"""Tests for the shared context dialog and widget behavior."""

from Qt import QtCore

from nscene.widgets.main_widget import FormedNukeContextDialog, NukeContextDialog, RestrictedLineEdit
from nscene.widgets.version_edit import VersionLineEdit


def test_restricted_line_edit_normalizes_programmatic_and_user_text(qapp, qtbot):
    """Normalize case and path characters for both entry paths."""
    edit = RestrictedLineEdit()
    edit.setText("A Shot.v1")
    assert edit.text() == "a_shot_v1"
    qtbot.addWidget(edit)
    edit.clear()
    edit.show()
    qtbot.keyClicks(edit, "HELLO World")
    assert edit.text() == "hello_world"


def test_context_and_save_field_visibility(qapp):
    """Toggle context and save-only fields independently."""
    widget = NukeContextDialog()
    widget.show()
    widget.set_context_fields_visible(False)
    widget.set_save_fields_visible(False)
    assert not widget.project_edit.isVisible()
    assert not widget.description_container.isVisible()
    widget.set_context_fields_visible(True)
    widget.set_save_fields_visible(True)
    assert widget.project_edit.isVisible()
    assert widget.description_container.isVisible()
    widget.close()


def test_settings_restore_and_partial_history(qapp, tmp_path):
    """Restore form values and save partial project context."""
    projects = tmp_path / "projects"
    (projects / "show").mkdir(parents=True)
    first = FormedNukeContextDialog(projects_root=str(projects), show=False)
    first.base_widget.project_edit.setText("show")
    first.base_widget.description_edit.setText("Comp Test")
    first.save_settings()
    assert first._read_history()[0] == ("show", "", "")
    second = FormedNukeContextDialog(projects_root=str(projects), show=False)
    assert second.base_widget.project_edit.text() == "show"
    assert second.base_widget.description_edit.text() == "comp_test"
    assert second._read_history().count(("show", "", "")) == 1
    first.close()
    second.close()


def test_history_deduplicates_and_limits(qapp, tmp_path):
    """Move duplicate history to the front and retain only the configured limit."""
    form = FormedNukeContextDialog(projects_root=str(tmp_path), show=False)
    assert form.record_context(("a", "b", "c"))
    assert form.record_context(("x", "y", "z"))
    assert form.record_context(("a", "b", "c"))
    history = form._read_history()
    assert history[:2] == [("a", "b", "c"), ("x", "y", "z")]
    for number in range(form.HISTORY_LIMIT + 5):
        form.record_context((f"project{number}", "", ""))
    assert len(form._read_history()) == form.HISTORY_LIMIT
    assert not form.record_context(("", "", ""))
    form.close()


def test_record_script_context_ignores_nuke_directory(qapp, tmp_path):
    """Infer project, sequence, and shot from a Nuke script location."""
    projects = tmp_path / "projects"
    form = FormedNukeContextDialog(projects_root=str(projects), show=False)
    script = projects / "show" / "seq" / "shot" / "nuke" / "comp.nk"
    assert form.record_script_context(str(script))
    assert form._read_history()[0] == ("show", "seq", "shot")
    form.close()


def test_autosave_option_persists_and_paste_action_selection(qapp, tmp_path):
    """Persist autosave visibility and enable paste only for one script."""
    script = tmp_path / "scene.nk"
    script.write_text("", encoding="utf-8")
    form = FormedNukeContextDialog(projects_root=str(tmp_path), show=False)
    action = form.base_widget.show_autosaves_action
    action.setChecked(True)
    assert form.settings.value("show_autosaves", False, type=bool)
    assert form.base_widget.script_tree._show_autosaves
    index = form.base_widget.script_tree.file_model.index(str(script))
    form.base_widget.script_tree.selectionModel().select(
        index,
        QtCore.QItemSelectionModel.SelectionFlag.ClearAndSelect | QtCore.QItemSelectionModel.SelectionFlag.Rows,
    )
    form._update_paste_action()
    assert form.base_widget.paste_selected_action.isEnabled()
    form.base_widget.script_tree.selectionModel().clearSelection()
    form._update_paste_action()
    assert not form.base_widget.paste_selected_action.isEnabled()
    form.close()


def test_version_line_edit_emits_up_down_steps(qapp, qtbot):
    """Emit signed version changes for arrow key input."""
    edit = VersionLineEdit()
    qtbot.addWidget(edit)
    edit.show()
    with qtbot.waitSignal(edit.versionStep) as signal:
        qtbot.keyClick(edit, QtCore.Qt.Key.Key_Up)
    assert signal.args == [1]
    with qtbot.waitSignal(edit.versionStep) as signal:
        qtbot.keyClick(edit, QtCore.Qt.Key.Key_Down)
    assert signal.args == [-1]
