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
    "import nscene.interface as nscene_interface; nscene_interface.save_in_application()",
    "ctrl+s",
    "SaveAs.png",
    index=1,
)
