"""Rez build script using uv for package installation."""

import os
import shutil
import subprocess
from pathlib import Path


def build() -> None:
    source_path = Path(os.environ["REZ_BUILD_SOURCE_PATH"]).resolve()
    install_enabled = os.environ.get("REZ_BUILD_INSTALL") == "1"

    if not install_enabled:
        # Rez may invoke a non-install build phase first; nothing to do here.
        return

    install_path = Path(os.environ["REZ_BUILD_INSTALL_PATH"]).resolve()
    target_path = install_path / "python"
    target_path.mkdir(parents=True, exist_ok=True)

    cmd = [
        "uv",
        "pip",
        "install",
        ".",
        "--no-deps",
        "--target",
        str(target_path),
    ]
    subprocess.run(cmd, cwd=source_path, check=True)
    # Copy nuke in the source directory to the target path
    nuke_source = source_path / "src/nuke"
    shutil.copytree(nuke_source, install_path / "nuke", dirs_exist_ok=True)


if __name__ == "__main__":
    build()
