"""Tests for public interface routes and save dispatch."""

from types import SimpleNamespace

import pytest

from nscene import interface, view


def test_public_entry_points_and_compatibility_aliases(monkeypatch):
    """Route public API functions to their implementation modules."""
    open_view = object()
    save_view = object()
    monkeypatch.setattr(interface._open_interface, "load_in_application", lambda: open_view)
    monkeypatch.setattr(interface._save_interface, "load_in_application", lambda: save_view)
    assert interface.open_in_application() is open_view
    assert interface.save_in_application() is save_view
    assert interface.save_as_in_application() is save_view
    assert interface.load_in_application is interface.save_in_application
    assert view.open_in_application is interface.open_in_application
    assert view.save_as_in_application is interface.save_as_in_application


def test_save_or_save_as_for_unsaved_script(monkeypatch, fake_nuke):
    """Open Save As for an unnamed Nuke root."""
    expected = object()
    monkeypatch.setattr(interface, "save_in_application", lambda: expected)
    assert interface.save_or_save_as_in_application() is expected


@pytest.mark.parametrize("name", ["", "Root", "Untitled"])
def test_save_or_save_as_for_all_unsaved_names(monkeypatch, fake_nuke, name):
    """Treat each Nuke unsaved-root sentinel as a request for Save As."""
    fake_nuke.root = lambda: SimpleNamespace(name=lambda: name)
    expected = object()
    monkeypatch.setattr(interface, "save_in_application", lambda: expected)
    assert interface.save_or_save_as_in_application() is expected
    assert fake_nuke.calls == []


def test_save_or_save_as_saves_existing_script(fake_nuke):
    """Save an already named script directly without opening the dialog."""
    fake_nuke.root = lambda: SimpleNamespace(name=lambda: "/projects/show/comp.nk")
    assert interface.save_or_save_as_in_application() is True
    assert fake_nuke.calls == [("scriptSave",)]
