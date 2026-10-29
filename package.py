"""Rez package definition for nscene."""

import subprocess

name = "nscene"
version = subprocess.check_output(["rezops-get-version"]).decode().strip()
description = "Nuke save as and open with path management."
requires = [
    "necessities",
    "nuke",
    "python-3.9+<4",
    "Qt.py-2+<3",
]
private_build_requires = []
build_command = f"rezops-build {name}"


def commands():
    """Expose the generated package and optional Nuke tools in Rez."""
    env.PYTHONPATH.append("{root}/python")  # noqa: F821 -- Rez injects ``env`` at runtime.
    env.NUKE_PATH.append("{root}/src/nuke")  # noqa: F821 -- Rez injects ``env`` at runtime.
