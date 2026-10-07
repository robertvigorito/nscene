"""The nscene menu integration for Nuke."""

import nuke


nuke.menu("Nuke").addCommand(
    "File/Save As", "import nscene.save_as_interface as nv; view = nv.load_in_application()", "alt+shift+s"
)
