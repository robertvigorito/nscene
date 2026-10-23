"""Tests for Open dialog context-menu actions."""

from Qt import QtCore, QtGui, QtWidgets

from nscene import open_interface


def test_context_menu_actions(qapp, monkeypatch, tmp_path, fake_nuke):
    """Dispatch open, paste, browser, copy, and folder actions from the tree menu."""
    monkeypatch.setattr(open_interface, "get_projects_root", lambda: str(tmp_path))
    monkeypatch.setattr(open_interface, "current_package_root", lambda _root: str(tmp_path))
    view = open_interface.NukeOpenInterface()
    script = tmp_path / "scene.nk"
    script.write_text("", encoding="utf-8")
    tree = view._base_widget.script_tree
    view._base_widget.hide()
    tree.set_directory(str(tmp_path))
    index = tree.file_model.index(str(script))
    monkeypatch.setattr(type(tree), "indexAt", lambda _self, _position: index)
    calls = []
    view.open_script = lambda path: calls.append(("open", path)) or True
    view.insert_script_as_drop = lambda path, **kwargs: calls.append(("paste", path, kwargs)) or True
    view.set_script_directory_root = lambda path: calls.append(("browser-root", path)) or True
    view.set_nuke_root_name = lambda path: calls.append(("root-name", path)) or True
    monkeypatch.setattr(QtGui.QDesktopServices, "openUrl", lambda url: calls.append(("folder", url.toLocalFile())))
    action_name = ""

    class FakeAction:
        def __init__(self, text):
            self.text = text
            self.enabled = True

        def setEnabled(self, enabled):
            self.enabled = enabled

    class FakeMenu:
        def __init__(self, _parent):
            self.menu_actions = []

        def addAction(self, text):
            action = FakeAction(text)
            self.menu_actions.append(action)
            return action

        def addSeparator(self):
            return None

        def exec(self, _position):
            return next(action for action in self.menu_actions if action.text == action_name)

    monkeypatch.setattr(open_interface.QtWidgets, "QMenu", FakeMenu)
    position = QtCore.QPoint(0, 0)
    for action_name in (
        "Open",
        "Insert as Drop",
        "Insert as Drop Group",
        "Set Browser Root Here",
        "Set Root Name to Path",
        "Copy Path",
        "Copy File Name",
        "Copy Folder Path",
        "Open Containing Folder",
    ):
        view._show_script_context_menu(position)

    assert calls[:5] == [
        ("open", str(script)),
        ("paste", str(script), {}),
        ("paste", str(script), {"into_group": True}),
        ("browser-root", str(script)),
        ("root-name", str(script)),
    ]
    assert QtWidgets.QApplication.clipboard().text() == str(tmp_path)
    assert calls[-1] == ("folder", str(tmp_path))
    view.close()
