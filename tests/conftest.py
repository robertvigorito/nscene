"""Shared fixtures for headless Qt and mocked Nuke tests."""

import os
import sys
import types

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from Qt import QtCore, QtWidgets


@pytest.fixture(scope="session")
def qapp():
    """Provide a Qt application for widget tests.

    Returns:
        QApplication: The shared application instance.
    """
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


@pytest.fixture(autouse=True)
def isolated_qsettings(tmp_path, monkeypatch):
    """Keep QSettings isolated between tests.

    Args:
        tmp_path: Temporary directory fixture.
        monkeypatch: Pytest monkeypatch fixture.

    Returns:
        None: Settings storage is redirected for the current test.
    """
    QtCore.QSettings.setDefaultFormat(QtCore.QSettings.Format.IniFormat)
    QtCore.QSettings.setPath(QtCore.QSettings.Format.IniFormat, QtCore.QSettings.Scope.UserScope, str(tmp_path))
    QtCore.QSettings.setPath(QtCore.QSettings.Format.IniFormat, QtCore.QSettings.Scope.SystemScope, str(tmp_path))
    settings = QtCore.QSettings("nscene", "save-as")
    settings.clear()
    settings.sync()


@pytest.fixture
def fake_nuke(monkeypatch):
    """Install a minimal Nuke module that tests can customize.

    Args:
        monkeypatch: Pytest monkeypatch fixture.

    Returns:
        SimpleNamespace: Fake module that records Nuke API calls.
    """
    calls = []
    fake_module = types.ModuleType("nuke")
    fake_module.calls = calls
    root = types.SimpleNamespace(name=lambda: "Untitled")
    fake_module.root = lambda: root
    fake_module.scriptOpen = lambda path: calls.append(("scriptOpen", path))
    fake_module.scriptSave = lambda: calls.append(("scriptSave",))
    fake_module.scriptSaveAs = lambda path: calls.append(("scriptSaveAs", path))
    fake_module.scriptClear = lambda: calls.append(("scriptClear",))
    fake_module.nodePaste = lambda path: calls.append(("nodePaste", path))
    fake_module.collapseToGroup = lambda: None
    monkeypatch.setitem(sys.modules, "nuke", fake_module)
    return fake_module
