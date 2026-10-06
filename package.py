"""Minimal Rez package definition for nscene."""


def _read_project_meta():
    version_value = "0.0.0"
    description_value = ""
    in_project = False

    with open("pyproject.toml", "r", encoding="utf-8") as stream:
        for raw_line in stream:
            line = raw_line.strip()

            if line == "[project]":
                in_project = True
                continue

            if in_project and line.startswith("["):
                break

            if not in_project or "=" not in line:
                continue

            if line.startswith("version"):
                version_value = line.split("=", 1)[1].strip().strip('"').strip("'")
            elif line.startswith("description"):
                description_value = line.split("=", 1)[1].strip().strip('"').strip("'")

    return {
        "version": version_value,
        "description": description_value,
    }


_meta = _read_project_meta()

name = "nscene"
version = _meta["version"]
description = _meta["description"]

authors = []
requires = ["python", "nuke", "Qt.py", "necessities"]
private_build_requires = []

build_command = "{root}/bin/rezbuild"


def commands():
    python_root = root + "/python"
    nuke_menu_root = root + "/nuke"

    env.PYTHONPATH.append(python_root)
    env.NUKE_PATH.append(nuke_menu_root)
