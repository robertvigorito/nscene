"""Rez build script using uv for package installation."""

import os
import shutil
import subprocess
from pathlib import Path


def build() -> None:
    source_path = Path(os.environ["REZ_BUILD_SOURCE_PATH"]).resolve()
    install_enabled = os.environ.get("REZ_BUILD_INSTALL") == "1"
    print(f"Install enabled: {install_enabled}")

    install_path = Path(os.environ["REZ_BUILD_INSTALL_PATH"]).resolve()
    target_path = install_path / "python"
    target_path.mkdir(parents=True, exist_ok=True)
    if not install_enabled:
        # symlink the source directory to the target path
        if target_path.exists():
            shutil.rmtree(target_path, ignore_errors=True)
            target_path.unlink(missing_ok=True)
        (target_path / source_path.name).parent.mkdir(parents=True, exist_ok=True)
        (target_path / source_path.name).symlink_to(source_path / "src" / source_path.name)
        print(f"Symlinked {source_path} to {target_path}")
        return
    
    shutil.rmtree(target_path, ignore_errors=True)
    target_path.unlink(missing_ok=True)
    cmd = [
        "uv",
        "pip",
        "install",
        ".",
        "--no-deps",
        "--target",
        str(target_path),
    ]
    print("install to", target_path)
    subprocess.run(cmd, cwd=source_path, check=True)
    # Copy nuke in the source directory to the target path
    nuke_source = source_path / "src/nuke"
    shutil.copytree(nuke_source, install_path / "nuke", dirs_exist_ok=True)


if __name__ == "__main__":
    build()
