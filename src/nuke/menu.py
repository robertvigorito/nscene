"""The nscene menu integration for Nuke."""

import nuke

nuke.menu("Nuke").addCommand(
    "File/WGID Open",
    "import nscene.interface as nscene_interface; nscene_interface.open_in_application()",
    "ctrl+o",
    "Open.png",
    index=0,
)

nuke.menu("Nuke").addCommand(
    "File/WGID Save As",
    "import nscene.interface as nscene_interface; nscene_interface.save_as_in_application()",
    "ctrl+shift+s",
    "SaveAs.png",
    index=1,
)
nuke.menu("Nuke").addCommand(
    "File/WGID Save Comp",
    "import nscene.interface as nscene_interface; nscene_interface.save_or_save_as_in_application()",
    "ctrl+s",
    "Save.png",
    index=2,
)
