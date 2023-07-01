import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QGraphicsScene, QGraphicsView, QGraphicsItem,
                             QDockWidget, QWidget, QListWidget, QPushButton, QGridLayout, QShortcut, QSizePolicy)
from PyQt5.QtGui import QImage, QPixmap, QColor, QPainter, QPen, QFont, QTransform, QKeySequence, QPalette, QBrush
from PyQt5.QtCore import Qt, QPoint, QRect


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setFont(QFont('Segoe UI', 12))
        #  pal = self.palette()
        #  pal.setBrush(QPalette.Window, QBrush(QColor(0, 255, 255), Qt.SolidPattern))
        #  self.setPalette(pal)

        self.layout = QGridLayout()
        self.setLayout(self.layout)

        # self.canvas = QImage(self.size(), QImage.Format_ARGB32_Premultiplied)
        # self.canvas.fill(QColor(255, 0, 0, alpha=0))

        self.currentLayer = 0
        # Будет перемещена в кастомный виджет растрового слоя
        # self.lastMousePos = QPoint(0, 0)
        self.resolution = 720, 720

        self.layout.addWidget(QPushButton("Новый растровый слой", self), 0, 0)
        self.layout.addWidget(QListWidget(), 1, 0)
        self.layout.addWidget(PreviewWidget(self), 1, 1, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(QPushButton('3'), 0, 1)
        self.layout.setColumnStretch(1, 1)

        self.layout.itemAtPosition(0, 0).widget().clicked.connect(self.newBitmapLayer)

        self.zoomInShortcut = QShortcut(QKeySequence('Ctrl+='), self)
        self.zoomInShortcut.activated.connect(self.zoomIn)

        self.zoomOutShortcut = QShortcut(QKeySequence('Ctrl+-'), self)
        self.zoomOutShortcut.activated.connect(self.zoomOut)

        self.scene = QGraphicsScene(self)
        self.scene.addPixmap(QPixmap('checkerboard.png').scaled(*self.resolution, aspectRatioMode=Qt.IgnoreAspectRatio))
        self.layout.itemAtPosition(1, 1).widget().setScene(self.scene)

        self.show()

    def zoomIn(self):
        self.layout.itemAtPosition(1, 1).widget().scale(1.25, 1.25)

    def zoomOut(self):
        self.layout.itemAtPosition(1, 1).widget().scale(0.8, 0.8)

    def resizeEvent(self, event):
        self.layout.itemAtPosition(1, 1).widget().setGeometry(
            QRect(self.layout.itemAtPosition(0, 1).geometry().topLeft().x(),
                  self.layout.itemAtPosition(1, 0).geometry().topLeft().y(),
                  self.layout.itemAtPosition(0, 1).geometry().width(),
                  self.layout.itemAtPosition(1, 0).geometry().height()))

    def newBitmapLayer(self):
        self.scene.addWidget(BitmapLayer(*self.resolution))
        self.layout.itemAtPosition(1, 0).widget().addItem('Новый растровый слой')


class PreviewWidget(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)


class BitmapLayer(QWidget):
    def __init__(self, width, height):
        super().__init__()
        self.setMinimumSize(width, height)
        self.setMaximumSize(width, height)
        self.resolution = width, height
        self.active = False

        pal = self.palette()
        pal.setBrush(QPalette.Window, QBrush(QColor(0, 0, 0, alpha=128), Qt.SolidPattern))
        self.setPalette(pal)

    def paintEvent(self, event):
        qp = QPainter(self)
        qp.setPen(Qt.blue)
        qp.setBrush(QBrush(QColor(255, 0, 0), Qt.SolidPattern))
        qp.drawLine(0, 0, *self.resolution)
        qp.drawLine(0, self.resolution[1], self.resolution[0], 0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())