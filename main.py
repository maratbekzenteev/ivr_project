import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QGraphicsScene
from PyQt5.QtGui import QImage, QColor, QPainter, QPen, QFont
from PyQt5.QtCore import Qt, QPoint


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(0, 0, 1280, 720)
        self.setFont(QFont('Segoe UI', 12))

        self.canvas = QImage(self.size(), QImage.Format_ARGB32_Premultiplied)
        self.canvas.fill(QColor(255, 0, 0, alpha=0))

        self.drawing = False
        self.currentLayer = 0
        self.lastMousePos = QPoint(0, 0)

        self.coords = QLabel(self)
        self.coords.setText('0 0')
        self.coords.setGeometry(0, 0, 200, 32)

        # print(QPoint(2, 0) + QPoint(1, 20))
        print(self.pos().x(), self.pos().y())

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.lastMousePos = event.pos()

    def mouseMoveEvent(self, event) -> None:
        if event.buttons() & Qt.LeftButton & self.drawing:
            self.coords.setText(f'{self.lastMousePos.x()} {self.lastMousePos.y()} {event.pos().x()} {event.pos().y()}')

            painter = QPainter(self.canvas)
            painter.setPen(QPen(QColor(0, 0, 0), 10, Qt.SolidLine, Qt.RoundCap, Qt.BevelJoin))

            painter.drawLine(self.lastMousePos, event.pos())
            self.lastMousePos = event.pos()

            self.update()

    def mouseReleaseEvent(self, event) -> None:
        if event.button == Qt.LeftButton:
            self.drawing = False

    def paintEvent(self, event):
        canvasPainter = QPainter(self)
        canvasPainter.drawImage(self.rect(), self.canvas)




if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())