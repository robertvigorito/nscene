"""Tests for the filesystem script tree."""

from PySide6 import QtCore, QtGui

from nscene.widgets.script_tree import ExistingScriptsTreeView, _grayscale_pixmap


def test_script_file_recognition():
    """Recognize regular Nuke scripts and autosaves case-insensitively."""
    assert ExistingScriptsTreeView.is_script_file("/tmp/a.nk")
    assert ExistingScriptsTreeView.is_script_file("/tmp/A.NK.AUTOSAVE")
    assert not ExistingScriptsTreeView.is_script_file("/tmp/a.txt")


def test_autosave_filter_toggle(qapp, tmp_path):
    """Include autosaves only when the option is enabled."""
    tree = ExistingScriptsTreeView()
    assert tree.file_model.nameFilters() == ["*.nk"]
    tree.set_show_autosaves(True)
    assert tree.file_model.nameFilters() == ["*.nk", "*.nk.autosave"]
    tree.set_show_autosaves(False)
    assert tree.file_model.nameFilters() == ["*.nk"]
    tree.close()


def test_tree_directory_and_headers(qapp, tmp_path):
    """Set and clear filesystem roots and expose expected column labels."""
    script = tmp_path / "comp.nk"
    script.write_text("", encoding="utf-8")
    tree = ExistingScriptsTreeView()
    tree.set_directory(str(tmp_path))
    assert tree.file_model.rootPath() == str(tmp_path)
    assert tree.HEADER_TITLES == ("Script", "Size", "Type", "Modified")
    tree.set_save_path(str(tmp_path / "new.nk"))
    assert tree.file_model.rootPath() == str(tmp_path)
    tree.clear_directory()
    assert not tree.rootIndex().isValid()
    tree.close()


def test_grayscale_pixmap_preserves_alpha(qapp):
    """Convert icon colors to grayscale without changing transparency."""
    pixmap = QtGui.QPixmap(1, 1)
    pixmap.fill(QtGui.QColor(255, 0, 0, 128))
    gray = _grayscale_pixmap(pixmap).toImage().pixelColor(0, 0)
    assert gray.red() == gray.green() == gray.blue()
    assert gray.alpha() == 128


def test_start_drag_provides_script_urls(qapp, monkeypatch, tmp_path, fake_nuke):
    """Start a copy drag carrying local script URLs and text paths."""
    script = tmp_path / "comp.nk"
    script.write_text("", encoding="utf-8")
    tree = ExistingScriptsTreeView()
    tree.set_directory(str(tmp_path))
    index = tree.file_model.index(str(script))
    tree.selectionModel().select(
        index,
        QtCore.QItemSelectionModel.SelectionFlag.ClearAndSelect | QtCore.QItemSelectionModel.SelectionFlag.Rows,
    )
    captured = []
    monkeypatch.setattr(QtGui.QDrag, "exec", lambda _drag, action: captured.append(action))
    tree.startDrag(QtCore.Qt.DropAction.CopyAction)
    assert captured == [QtCore.Qt.DropAction.CopyAction]
    tree.close()
