"""Shared project-path configuration and Nuke script path helpers."""

import platform
from pathlib import Path

PROJECTS_ROOTS = {
    "Linux": "/mnt/e/wgid/projects",
    "Windows": "e:/wgid/projects",
}


def get_projects_root() -> str:
    """Return the projects root path for the current operating system.

    Returns:
        The Windows drive path or its Linux mount path.
    """
    operating_system = platform.system()
    try:
        return PROJECTS_ROOTS[operating_system]
    except KeyError as error:
        raise OSError(f"Unsupported operating system for project path: {operating_system}") from error


def current_package_root(projects_root: str | None = None) -> str:
    """Find the project package containing the current saved Nuke script.

    Args:
        projects_root: Root directory containing project packages. Defaults to the platform-specific root.

    Returns:
        The containing package path, or the configured projects root if it cannot be determined.
    """
    projects_root = projects_root or get_projects_root()
    try:
        import nuke

        script_path = nuke.root().name()
    except (ImportError, AttributeError, RuntimeError):
        script_path = ""

    if not script_path or script_path in {"Root", "Untitled"}:
        return projects_root

    current_script = Path(script_path).expanduser()
    root_path = Path(projects_root).expanduser()
    if current_script.suffix.lower() != ".nk":
        return projects_root

    try:
        relative_script = current_script.relative_to(root_path)
    except ValueError:
        return str(current_script.parent)

    if not relative_script.parts:
        return projects_root

    package_root = root_path / relative_script.parts[0]
    return str(package_root) if package_root.is_dir() else projects_root
