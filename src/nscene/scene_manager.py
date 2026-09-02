"""Filesystem and Nuke operations used by the scene browser."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

_SCENE_NAME = re.compile(
    r"^(?P<name>.+?)_v(?P<version>\d{3})_m(?P<minor>\d{2})(?:_(?P<description>.*?))?\.nk$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class SceneRecord:
    path: Path
    name: str
    version: int
    minor: int
    description: str
    created: datetime
    modified: datetime

    @property
    def version_label(self) -> str:
        return f"v{self.version:03d}.{self.minor:02d}"


class SceneRepository:
    """Stores scenes below ``root/project/sequence/shot/type``."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).expanduser()

    def directory(self, project: str, sequence: str, shot: str, scene_type: str) -> Path:
        values = (project, sequence, shot, scene_type)
        if any(not value or Path(value).name != value for value in values):
            raise ValueError("Project, sequence, shot, and type must be simple names")
        return self.root.joinpath(*values)

    def list_scenes(
        self, project: str, sequence: str, shot: str, scene_type: str
    ) -> list[SceneRecord]:
        directory = self.directory(project, sequence, shot, scene_type)
        if not directory.is_dir():
            return []
        records: list[SceneRecord] = []
        for path in directory.glob("*.nk"):
            match = _SCENE_NAME.match(path.name)
            if not match:
                continue
            stat = path.stat()
            records.append(
                SceneRecord(
                    path=path,
                    name=match.group("name"),
                    version=int(match.group("version")),
                    minor=int(match.group("minor")),
                    description=match.group("description") or "",
                    created=datetime.fromtimestamp(stat.st_ctime),
                    modified=datetime.fromtimestamp(stat.st_mtime),
                )
            )
        return sorted(records, key=lambda item: (item.version, item.minor), reverse=True)

    def next_version(
        self, project: str, sequence: str, shot: str, scene_type: str, name: str,
    ) -> tuple[int, int]:
        records = [record for record in self.list_scenes(project, sequence, shot, scene_type)
                   if record.name == name]
        if not records:
            return 1, 0
        latest = max(records, key=lambda item: (item.version, item.minor))
        return latest.version, latest.minor + 1

    def save_path(
        self, project: str, sequence: str, shot: str, scene_type: str,
        name: str, version: int, minor: int, description: str = "",
    ) -> Path:
        if not name or Path(name).name != name or not re.fullmatch(r"[\w.-]+", name):
            raise ValueError("Name must contain only letters, numbers, _, ., or -")
        if version < 0 or minor < 0:
            raise ValueError("Version numbers cannot be negative")
        suffix = f"_{description.strip()}" if description.strip() else ""
        return self.directory(project, sequence, shot, scene_type) / (
            f"{name}_v{version:03d}_m{minor:02d}{suffix}.nk"
        )

    def record_scene(
        self, project: str, sequence: str, shot: str, scene_type: str,
        path: Path, created: datetime | None = None,
    ) -> None:
        """Hook for repositories that persist scene metadata."""


class MongoSceneRepository(SceneRepository):
    """MongoDB metadata index backed by the same scene path convention."""

    def __init__(
        self,
        root: str | Path,
        uri: str,
        database: str = "nscene",
        collection: str = "scenes",
    ) -> None:
        super().__init__(root)
        try:
            from pymongo import MongoClient
        except ImportError as exc:
            raise RuntimeError("PyMongo is required for the MongoDB backend") from exc
        self._client = MongoClient(uri, serverSelectionTimeoutMS=3000)
        self._collection = self._client[database][collection]
        self._collection.create_index(
            [("project", 1), ("sequence", 1), ("shot", 1), ("scene_type", 1)]
        )

    def list_scenes(
        self, project: str, sequence: str, shot: str, scene_type: str
    ) -> list[SceneRecord]:
        records: list[SceneRecord] = []
        query = {
            "project": project,
            "sequence": sequence,
            "shot": shot,
            "scene_type": scene_type,
        }
        for document in self._collection.find(query):
            path = Path(document["path"])
            stat = path.stat() if path.is_file() else None
            created = document.get("created") or (
                datetime.fromtimestamp(stat.st_ctime) if stat else datetime.min
            )
            modified = document.get("modified") or (
                datetime.fromtimestamp(stat.st_mtime) if stat else created
            )
            records.append(
                SceneRecord(
                    path=path,
                    name=document["name"],
                    version=int(document["version"]),
                    minor=int(document["minor"]),
                    description=document.get("description", ""),
                    created=created,
                    modified=modified,
                )
            )
        return sorted(records, key=lambda item: (item.version, item.minor), reverse=True)

    def record_scene(
        self, project: str, sequence: str, shot: str, scene_type: str,
        path: Path, created: datetime | None = None,
    ) -> None:
        match = _SCENE_NAME.match(path.name)
        if not match:
            raise ValueError(f"Not a versioned Nuke scene path: {path.name}")
        modified = datetime.fromtimestamp(path.stat().st_mtime)
        self._collection.update_one(
            {"path": str(path)},
            {"$set": {
                "project": project,
                "sequence": sequence,
                "shot": shot,
                "scene_type": scene_type,
                "path": str(path),
                "name": match.group("name"),
                "version": int(match.group("version")),
                "minor": int(match.group("minor")),
                "description": match.group("description") or "",
                "created": created or datetime.fromtimestamp(path.stat().st_ctime),
                "modified": modified,
            }},
            upsert=True,
        )


class NukeAdapter:
    """Small adapter that keeps the UI testable outside a running Nuke session."""

    def __init__(self, nuke_module: Any | None = None) -> None:
        if nuke_module is None:
            try:
                import nuke as nuke_module  # type: ignore[import-not-found]
            except ImportError as exc:
                raise RuntimeError("The Nuke Python module is required for this action") from exc
        self.nuke = nuke_module

    def save_as(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.nuke.scriptSaveAs(str(path))

    def open(self, path: Path) -> None:
        self.nuke.scriptOpen(str(path))

    def copy_to_group(self, path: Path) -> None:
        self.nuke.nodePaste(str(path))


def choices(values: Iterable[str]) -> list[str]:
    """Return sorted unique non-empty choices for UI comboboxes."""
    return sorted({value for value in values if value})
