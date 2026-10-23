"""Tests for platform-aware project paths."""

from types import SimpleNamespace

import pytest

from nscene import paths


def test_projects_root_for_linux_and_windows(monkeypatch):
    """Select the configured root for supported platforms."""
    monkeypatch.setattr(paths.platform, "system", lambda: "Linux")
    assert paths.get_projects_root() == "/mnt/e/wgid/projects"
    monkeypatch.setattr(paths.platform, "system", lambda: "Windows")
    assert paths.get_projects_root() == "e:/wgid/projects"


def test_projects_root_rejects_unknown_platform(monkeypatch):
    """Raise a clear error for unsupported platforms."""
    monkeypatch.setattr(paths.platform, "system", lambda: "Darwin")
    with pytest.raises(OSError, match="Unsupported operating system"):
        paths.get_projects_root()


def test_normalize_windows_path(monkeypatch):
    """Strip the spurious leading slash from drive paths on Windows only."""
    monkeypatch.setattr(paths.platform, "system", lambda: "Windows")
    assert paths.normalize_platform_path("/E:/projects/a.nk") == "E:/projects/a.nk"
    monkeypatch.setattr(paths.platform, "system", lambda: "Linux")
    assert paths.normalize_platform_path("/mnt/e/a.nk") == "/mnt/e/a.nk"


def test_current_package_root_from_nuke_script(tmp_path, monkeypatch, fake_nuke):
    """Find the project directory for a script under the projects root."""
    root = tmp_path / "projects"
    script = root / "show" / "seq" / "shot" / "nuke" / "comp.nk"
    script.parent.mkdir(parents=True)
    script.touch()
    monkeypatch.setattr(fake_nuke, "root", lambda: SimpleNamespace(name=lambda: str(script)))
    assert paths.current_package_root(str(root)) == str(root / "show")


@pytest.mark.parametrize("script_name", ["", "Root", "Untitled", "/outside/a.ma"])
def test_current_package_root_fallback(tmp_path, monkeypatch, fake_nuke, script_name):
    """Use the configured root when Nuke has no usable project script."""
    root = tmp_path / "projects"
    root.mkdir()
    monkeypatch.setattr(fake_nuke, "root", lambda: SimpleNamespace(name=lambda: script_name))
    assert paths.current_package_root(str(root)) == str(root)


def test_current_package_root_outside_projects(tmp_path, monkeypatch, fake_nuke):
    """Use a saved script's parent when it is outside the configured root."""
    script = tmp_path / "external" / "scene.nk"
    script.parent.mkdir()
    script.touch()
    monkeypatch.setattr(fake_nuke, "root", lambda: SimpleNamespace(name=lambda: str(script)))
    assert paths.current_package_root(str(tmp_path / "projects")) == str(script.parent)


def test_current_package_root_missing_package(tmp_path, monkeypatch, fake_nuke):
    """Avoid returning a nonexistent project directory."""
    root = tmp_path / "projects"
    root.mkdir()
    monkeypatch.setattr(fake_nuke, "root", lambda: SimpleNamespace(name=lambda: str(root / "missing" / "scene.nk")))
    assert paths.current_package_root(str(root)) == str(root)
