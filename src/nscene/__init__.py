"""Nuke scene open/save browser."""

from .scene_manager import (
    MongoSceneRepository,
    NukeAdapter,
    SceneRecord,
    SceneRepository,
)

__all__ = ["MongoSceneRepository", "NukeAdapter", "SceneRecord", "SceneRepository", "main"]


def main() -> None:
    import os

    from .ui import show_open

    show_open(
        os.environ.get("NSCENE_SCENE_ROOT", "."),
        mongo_uri=os.environ.get("NSCENE_MONGO_URI"),
    )
