"""The nscene menu integration for Nuke."""

import nuke


nuke.menu("Nuke").addCommand("File/Save As", "import nscene.view as nv; view = nv.load_in_application()", "Ctrl+Shift+S")
