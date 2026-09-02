# nscene

PySide6 dialogs for saving and opening Nuke scenes using a configurable
`project/sequence/shot/type` directory layout.

```python
from nscene.ui import show_open, show_save_as

show_open("/show/scenes")
show_save_as("/show/scenes")
```

The open dialog lists matching `.nk` files with name, padded version (`v###.##`),
creation date, and modification date. It supports opening the selected script or
pasting it into the current Nuke group. The save dialog creates missing folders
and writes padded versioned filenames with an optional description.