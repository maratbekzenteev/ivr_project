import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtGui import QImage, QColor, QPainter, QPen
from PyQt5.QtCore import Qt, QPoint


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(0, 0, 1920, 1080)

        self.canvas = [QImage(self.size(), QImage.Format_ARGB32_Premultiplied)] * 2
        for canvas in self.canvas:
            canvas.fill(QColor(255, 0, 0, alpha=0))

        self.drawing = False
        self.currentLayer = 0
        self.lastMousePos = QPoint(0, 0)

        # print(QPoint(2, 0) + QPoint(1, 20))

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.lastMousePos = event.pos()

    def mouseMoveEvent(self, event) -> None:
        if event.buttons() & Qt.LeftButton & self.drawing:
            painter = QPainter(self.canvas[self.currentLayer])
            painter.setPen(QPen(QColor(0, 0, 0), 10, Qt.SolidLine, Qt.RoundCap, Qt.BevelJoin))

            painter.drawLine(self.lastMousePos, event.pos())
            self.lastMousePos = event.pos()

            self.update()

    def mouseReleaseEvent(self, event) -> None:
        if event.button == Qt.LeftButton:
            self.drawing = False

    def paintEvent(self, event):
        canvasPainter = QPainter(self)
        canvasPainter.drawImage(self.rect(), self.canvas[self.currentLayer], self.canvas[self.currentLayer].rect())




if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())