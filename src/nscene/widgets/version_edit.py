"""Version input widget with keyboard stepping support."""

from Qt import QtCore, QtGui, QtWidgets


class VersionLineEdit(QtWidgets.QLineEdit):
    """Line edit that signals when the user requests a version step."""

    versionStep = QtCore.Signal(int)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        """Emit version steps for the Up and Down arrow keys."""
        if event.key() == QtCore.Qt.Key.Key_Up:
            self.versionStep.emit(1)
            event.accept()
            return
        if event.key() == QtCore.Qt.Key.Key_Down:
            self.versionStep.emit(-1)
            event.accept()
            return
        super().keyPressEvent(event)
