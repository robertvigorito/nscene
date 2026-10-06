# nscene

Rez integration is configured to:

1. Use `uv` to install this package during `rez-build`
2. Skip automatic dependency installation (`--no-deps`)

## Requirements

- Rez available in your environment
- `uv` available on `PATH` for build time

## Build With Rez

From this repository root:

```bash
rez-build -i
```

This uses `package.py` and runs `bin/rezbuild`, which executes:

```bash
uv pip install . --no-deps --target <rez_install_root>/python
```

Dependencies are managed manually outside this Rez build step.

## Test Local Build With rez-env

Rebuild and install the package into your local Rez package repository:

```bash
REZ_DISABLE_MEMCACHE=1 rez-build -ci
```

Start a clean Rez shell with the package:

```bash
rez-env nscene
```

Inside that shell, verify imports and print where `nscene` was loaded from:

```bash
python -c "import nscene; print('nscene:', nscene.__file__); print('ok')"
```

You can also test the command entry point:

```bash
nscene
```

### Non-interactive one-liner

```bash
rez-env nscene -- python -c "import nscene; print(nscene.__file__)"
```

### If `rez-env nscene` cannot find the package

Check your configured Rez package paths:

```bash
rez-config packages_path
```

Temporarily prepend your local package path and try again:

```bash
REZ_PACKAGES_PATH=/home/robert-v/packages:$REZ_PACKAGES_PATH rez-env nscene -- python -c "import nscene; print(nscene.__file__)"
```

## Test Nuke Menu Injection From Rez

The Rez package sets these variables in context:

- `NUKE_PATH` includes the installed `nscene` package folder
- `NSCENE_REZ_MENU_TEST=1`

When running Rez in WSL and Nuke on Windows, the package now appends both:

- Linux paths (for WSL-native tools)
- Windows UNC `\\wsl$\<distro>\...` paths (for Windows Nuke)

Quick checks from shell:

```bash
rez-env nscene -- python -c "import os; print(os.getenv('NSCENE_REZ_MENU_TEST'))"
rez-env nscene -- python -c "import os; print(os.getenv('NUKE_PATH'))"
```

In Nuke launched from the same `rez-env nscene` context, look for:

- `NSCENE` menu
- `Rez Context Test` command

Clicking that command shows key Rez environment values.
