from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QImage, QColor, QPainter, QPen, QPalette, QBrush
from PyQt5.QtCore import Qt, QPoint


class BitmapLayer(QWidget):
    def __init__(self, width, height, parent):
        super().__init__()

        self.parent = parent

        self.setMinimumSize(width, height)
        self.setMaximumSize(width, height)
        self.resolution = width, height

        self.bitmap = QImage(self.size(), QImage.Format_ARGB32_Premultiplied)
        self.bitmap.fill(QColor(0, 0, 0, alpha=0))

        self.active = False
        self.drawing = False
        self.lastMousePos = QPoint(0, 0)

        self.pen = QPen(QColor(0, 0, 0), 10, Qt.SolidLine, Qt.RoundCap, Qt.BevelJoin)

        palette = self.palette()
        palette.setBrush(QPalette.Window, QBrush(QColor(0, 0, 0, alpha=0), Qt.SolidPattern))
        self.setPalette(palette)

    def paintEvent(self, event):
        qp = QPainter(self)
        qp.drawImage(0, 0, self.bitmap)

    def mousePressEvent(self, event):
        if not self.active:
            self.parent.scene.items()[self.parent.currentLayer + 1].widget().mousePressEvent(event)
        else:
            if event.button() == Qt.LeftButton and self.active:
                self.drawing = True
                self.lastMousePos = event.pos()

    def mouseMoveEvent(self, event):
        if not self.active:
            self.parent.scene.items()[self.parent.currentLayer + 1].widget().mouseMoveEvent(event)
        else:
            if event.buttons() & Qt.LeftButton & self.drawing & self.active:
                qp = QPainter(self.bitmap)
                qp.setPen(self.pen)

                qp.drawLine(self.lastMousePos, event.pos())
                self.lastMousePos = event.pos()

                self.update()

    def mouseReleaseEvent(self, event):
        if event.button == Qt.LeftButton:
            if self.active:
                self.drawing = False
            else:
                self.parent.scene.items()[self.parent.currentLayer + 1].widget().drawing = False

    def updateState(self, color):
        self.pen.setColor(color)