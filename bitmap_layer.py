from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QImage, QColor, QPainter, QPen, QPalette, QBrush
from PyQt5.QtCore import Qt, QPoint

class BitmapLayer(QWidget):
    def __init__(self, width, height):
        super().__init__()

        self.setMinimumSize(width, height)
        self.setMaximumSize(width, height)
        self.resolution = width, height

        self.bitmap = QImage(self.size(), QImage.Format_ARGB32_Premultiplied)
        self.bitmap.fill(QColor(0, 0, 0, alpha=0))

        self.active = False
        self.drawing = False
        self.lastMousePos = QPoint(0, 0)

        pal = self.palette()
        pal.setBrush(QPalette.Window, QBrush(QColor(0, 0, 0, alpha=128), Qt.SolidPattern))
        self.setPalette(pal)

    def paintEvent(self, event):
        qp = QPainter(self)
        qp.drawImage(0, 0, self.bitmap)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.lastMousePos = event.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton & self.drawing:
            qp = QPainter(self.bitmap)
            qp.setPen(QPen(QColor(0, 0, 0), 10, Qt.SolidLine, Qt.RoundCap, Qt.BevelJoin))

            qp.drawLine(self.lastMousePos, event.pos())
            self.lastMousePos = event.pos()

            self.update()

    def mouseReleaseEvent(self, event):
        if event.button == Qt.LeftButton:
            self.drawing = False