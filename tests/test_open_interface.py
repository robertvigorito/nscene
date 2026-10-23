"""Tests for Open dialog browsing and Nuke operations."""

from types import SimpleNamespace

from Qt import QtCore, QtWidgets

from nscene import open_interface


def make_open_interface(monkeypatch, tmp_path):
    """Construct an Open interface rooted at a temporary project tree."""
    monkeypatch.setattr(open_interface, "get_projects_root", lambda: str(tmp_path))
    monkeypatch.setattr(open_interface, "current_package_root", lambda _root: str(tmp_path))
    view = open_interface.NukeOpenInterface()
    view._base_widget.hide()
    return view


def test_context_navigation(qapp, monkeypatch, tmp_path):
    """Navigate at project, sequence, and shot depth, adding the Nuke folder at shot depth."""
    projects = tmp_path / "show" / "seq" / "shot" / "nuke"
    projects.mkdir(parents=True)
    view = make_open_interface(monkeypatch, tmp_path)
    view._base_widget.sequence_edit.clear()
    view._base_widget.shot_edit.clear()
    view._base_widget.project_edit.setText("show")
    assert view._base_widget.script_tree.file_model.rootPath() == str(tmp_path / "show")
    view._base_widget.sequence_edit.setText("seq")
    assert view._base_widget.script_tree.file_model.rootPath() == str(tmp_path / "show" / "seq")
    view._base_widget.shot_edit.setText("shot")
    assert view._base_widget.script_tree.file_model.rootPath() == str(projects)
    view.close()


def test_select_and_open_script_records_partial_context(qapp, monkeypatch, tmp_path, fake_nuke):
    """Open a selected script and record entered partial context before accepting the dialog."""
    view = make_open_interface(monkeypatch, tmp_path)
    script = tmp_path / "show" / "seq" / "shot" / "nuke" / "comp.nk"
    script.parent.mkdir(parents=True)
    script.write_text("", encoding="utf-8")
    view._base_widget.project_edit.setText("show")
    view._base_widget.sequence_edit.setText("seq")
    view._base_widget.shot_edit.setText("")
    assert view.open_script(str(script))
    assert fake_nuke.calls == [("scriptOpen", str(script))]
    assert view._form._read_history()[0] == ("show", "seq", "")
    assert view._base_widget.result() == QtWidgets.QDialog.DialogCode.Accepted
    view.close()


def test_open_infers_context_when_fields_blank(qapp, monkeypatch, tmp_path, fake_nuke):
    """Infer history context from the script path when no context was entered."""
    view = make_open_interface(monkeypatch, tmp_path)
    script = tmp_path / "show" / "seq" / "shot" / "nuke" / "comp.nk"
    script.parent.mkdir(parents=True)
    script.write_text("", encoding="utf-8")
    assert view._form.record_script_context(str(script))
    assert view._form._read_history()[0] == ("show", "seq", "shot")
    view._form.settings.remove("context_history")
    view._base_widget.project_edit.clear()
    view._base_widget.sequence_edit.clear()
    view._base_widget.shot_edit.clear()
    assert view.open_script(str(script))
    assert view._form._read_history()[0] == ("show", "seq", "shot")
    view.close()


def test_open_rejects_invalid_script_and_reports_failure(qapp, monkeypatch, tmp_path, fake_nuke):
    """Reject invalid paths and leave the dialog open after an Nuke error."""
    view = make_open_interface(monkeypatch, tmp_path)
    assert not view.open_script(str(tmp_path / "notes.txt"))
    script = tmp_path / "broken.nk"
    script.write_text("", encoding="utf-8")
    fake_nuke.scriptOpen = lambda _path: (_ for _ in ()).throw(RuntimeError("open error"))
    monkeypatch.setattr(QtWidgets.QMessageBox, "warning", lambda *_args: None)
    assert not view.open_script(str(script))
    assert view._base_widget.isVisible() is False
    view.close()


def test_root_navigation_and_root_name(qapp, monkeypatch, tmp_path, fake_nuke):
    """Set browser root and assign selected script path to Nuke's Root name knob."""
    view = make_open_interface(monkeypatch, tmp_path)
    script = tmp_path / "show" / "comp.nk"
    script.parent.mkdir(parents=True)
    script.write_text("", encoding="utf-8")
    assert not view.set_script_directory_root(str(tmp_path / "missing.nk"))
    assert view.set_script_directory_root(str(script))
    assert view._base_widget.script_tree.file_model.rootPath() == str(script.parent)

    root_name = {}
    root = {"name": SimpleNamespace(setValue=lambda value: root_name.update(value=value))}
    fake_nuke.root = lambda: root
    assert view.set_nuke_root_name(str(script))
    assert root_name["value"] == str(script)
    view.close()


def test_paste_selected_and_drop_group(qapp, monkeypatch, tmp_path, fake_nuke):
    """Paste selected scripts and label collapsed groups with script name and date."""
    view = make_open_interface(monkeypatch, tmp_path)
    script = tmp_path / "comp.nk"
    script.write_text("", encoding="utf-8")
    tree = view._base_widget.script_tree
    tree.set_directory(str(tmp_path))
    index = tree.file_model.index(str(script))
    tree.selectionModel().select(
        index,
        QtCore.QItemSelectionModel.SelectionFlag.ClearAndSelect | QtCore.QItemSelectionModel.SelectionFlag.Rows,
    )
    assert view.paste_selected_script()
    assert fake_nuke.calls[-1] == ("nodePaste", str(script))

    group_label = {}
    group = {"label": SimpleNamespace(setValue=lambda value: group_label.update(value=value))}
    fake_nuke.collapseToGroup = lambda: group
    assert view.insert_script_as_drop(str(script), into_group=True)
    assert group_label["value"].startswith("comp\n")
    assert not view.insert_script_as_drop(str(tmp_path / "invalid.txt"))
    view.close()


def test_script_drop_filter_accepts_local_nk(qapp, monkeypatch, tmp_path):
    """Accept only local dropped Nuke script files and delegate the first one."""
    view = make_open_interface(monkeypatch, tmp_path)
    script = tmp_path / "drop.nk"
    script.write_text("", encoding="utf-8")
    event = SimpleNamespace(
        mimeData=lambda: QtCore.QMimeData(),
        type=lambda: QtCore.QEvent.Type.Drop,
        acceptProposedAction=lambda: None,
    )
    mime_data = event.mimeData()
    mime_data.setUrls([QtCore.QUrl.fromLocalFile(str(script))])
    event.mimeData = lambda: mime_data
    called = []
    view.open_script = lambda path: called.append(path) or True
    assert view._drop_filter.eventFilter(view._base_widget, event)
    assert called == [str(script)]
    view.close()
