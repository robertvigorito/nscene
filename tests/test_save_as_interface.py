"""Tests for Save As behavior with mocked Nuke APIs."""

from Qt import QtWidgets

from nscene import save_as_interface


class FakeScene:
    """Minimal path assembler with replaceable field storage."""

    def __init__(self, **fields):
        self.fields = fields
        self.root = fields.get("root", "")
        self.show = fields.get("show", "")
        self.sequence = fields.get("sequence", "")
        self.shot = fields.get("shot", "")

    def replace(self, **fields):
        self.fields.update(fields)
        for name, value in fields.items():
            setattr(self, name, value)
        return self

    def resolve(self):
        sequence = f"/{self.sequence}" if self.sequence else ""
        shot = f"/{self.shot}" if self.shot else ""
        return f"{self.root}/{self.show}{sequence}{shot}/{self.fields['description']}_v001.00.nk"


def make_interface(monkeypatch, tmp_path):
    """Create the Save As interface with deterministic temporary project paths."""
    monkeypatch.setattr(save_as_interface, "get_projects_root", lambda: str(tmp_path))
    monkeypatch.setattr(
        save_as_interface._assemble.Scene, "from_application", lambda *_args, **kwargs: FakeScene(**kwargs)
    )
    return save_as_interface.NukeSaveAsInterface()


def fill_save_fields(interface, project="show", description="comp", sequence="", shot=""):
    """Populate the required Save As fields and optional hierarchy fields."""
    widget = interface.base_widget
    widget.project_edit.setText(project)
    widget.sequence_edit.setText(sequence)
    widget.shot_edit.setText(shot)
    widget.description_edit.setText(description)


def test_preview_requires_project_and_description_only(qapp, monkeypatch, tmp_path):
    """Allow a preview without sequence or shot, and reject missing required values."""
    interface = make_interface(monkeypatch, tmp_path)
    fill_save_fields(interface)
    assert interface._update_preview()
    assert "/show/comp_v001.00.nk" in interface.base_widget.preview_panel.text()
    fill_save_fields(interface, project="", description="comp")
    assert not interface._update_preview()
    fill_save_fields(interface, project="show", description="")
    assert not interface._update_preview()
    interface.close()


def test_save_creates_directory_and_calls_nuke(qapp, monkeypatch, tmp_path, fake_nuke):
    """Create target parent directories and save to the preview path."""
    interface = make_interface(monkeypatch, tmp_path)
    target = tmp_path / "show" / "nuke" / "comp.nk"
    interface._base_widget.set_preview_path(str(target))
    assert interface.save()
    assert target.parent.is_dir()
    assert fake_nuke.calls == [("scriptSaveAs", str(target))]


def test_save_directory_failure(qapp, monkeypatch, tmp_path, fake_nuke):
    """Return false and warn when the save directory cannot be created."""
    interface = make_interface(monkeypatch, tmp_path)
    interface._base_widget.set_preview_path("/dev/null/cannot-create/file.nk")
    monkeypatch.setattr(QtWidgets.QMessageBox, "warning", lambda *_args: None)
    assert not interface.save()
    assert fake_nuke.calls == []


def test_save_nuke_failure(qapp, monkeypatch, tmp_path, fake_nuke):
    """Report Nuke save failures without closing the dialog."""
    interface = make_interface(monkeypatch, tmp_path)
    interface._base_widget.set_preview_path(str(tmp_path / "fail.nk"))
    fake_nuke.scriptSaveAs = lambda _path: (_ for _ in ()).throw(RuntimeError("save error"))
    monkeypatch.setattr(QtWidgets.QMessageBox, "warning", lambda *_args: None)
    assert not interface.save()
    assert interface.base_widget.isVisible()


def test_clear_then_save(qapp, monkeypatch, tmp_path, fake_nuke):
    """Clear the current scene before saving the new target."""
    interface = make_interface(monkeypatch, tmp_path)
    target = tmp_path / "new" / "empty.nk"
    interface._base_widget.set_preview_path(str(target))
    assert interface.clear_script_and_save_as()
    assert fake_nuke.calls == [("scriptClear",), ("scriptSaveAs", str(target))]


def test_clear_failure_does_not_save(qapp, monkeypatch, tmp_path, fake_nuke):
    """Stop when Nuke cannot clear the current script."""
    interface = make_interface(monkeypatch, tmp_path)
    interface._base_widget.set_preview_path(str(tmp_path / "empty.nk"))
    fake_nuke.scriptClear = lambda: (_ for _ in ()).throw(RuntimeError("clear error"))
    monkeypatch.setattr(QtWidgets.QMessageBox, "warning", lambda *_args: None)
    assert not interface.clear_script_and_save_as()
    assert fake_nuke.calls == []


def test_paste_selected_script(qapp, monkeypatch, tmp_path, fake_nuke):
    """Paste the single selected Nuke script, rejecting non-script selections."""
    interface = make_interface(monkeypatch, tmp_path)
    script = tmp_path / "comp.nk"
    script.write_text("", encoding="utf-8")
    tree = interface.base_widget.script_tree
    tree.set_directory(str(tmp_path))
    index = tree.file_model.index(str(script))
    tree.selectionModel().select(
        index,
        tree.selectionModel().SelectionFlag.ClearAndSelect | tree.selectionModel().SelectionFlag.Rows,
    )
    assert interface.paste_selected_script()
    assert fake_nuke.calls[-1] == ("nodePaste", str(script))
    tree.selectionModel().clearSelection()
    assert not interface.paste_selected_script()
    interface.close()
