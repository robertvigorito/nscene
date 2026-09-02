# nscene

PySide6 dialogs for saving and opening Nuke scenes using a configurable
`project/sequence/shot/type` directory layout.

```python
from nscene.ui import show_open, show_save_as

show_open("/show/scenes", mongo_uri="mongodb://localhost:27017")
show_save_as("/show/scenes", mongo_uri="mongodb://localhost:27017")
```

The open dialog lists matching `.nk` files with name, padded version (`v###.##`),
creation date, and modification date. It supports opening the selected script or
pasting it into the current Nuke group. The save dialog creates missing folders
and writes padded versioned filenames with an optional description.

When `mongo_uri` is supplied, MongoDB stores and indexes the project, sequence,
shot, type, scene path, version, description, and timestamps. The files remain
on the filesystem; MongoDB is the searchable scene metadata backend. The
`nscene` command reads `NSCENE_MONGO_URI` and `NSCENE_SCENE_ROOT`.

## Installation

With [uv](https://docs.astral.sh/uv/):

```shell
uv sync
uv run nscene
```

The `pyproject.toml` is the source of dependency metadata; `uv sync` creates
the environment and lockfile for the current platform. Development tools can
be installed with `uv sync --group dev`.

With [Rez](https://github.com/AcademySoftwareFoundation/rez), install this
repository as a package (or add it to `REZ_PACKAGES_PATH`) and run:

```shell
rez-env nscene -- nscene
```

The Rez package supplies Python 3.12+, PySide6 6.8.1+, and adds `src` to
`PYTHONPATH`. Nuke must be present in the Rez context when using the dialogs.