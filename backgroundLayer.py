from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtCore import Qt


class BackgroundLayer(QWidget):
    def __init__(self, width, height):
        super().__init__()

        self.setMinimumSize(width, height)
        self.setMaximumSize(width, height)

        self.active = False

        self.pixmap = QPixmap("checkerboard.png").scaled(width, height, aspectRatioMode=Qt.IgnoreAspectRatio)

    def paintEvent(self, event):
        qp = QPainter(self)
        qp.drawPixmap(0, 0, self.pixmap)
