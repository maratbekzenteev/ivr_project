import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QGraphicsScene, QGraphicsView, QGraphicsItem,
                             QDockWidget, QWidget, QListWidget, QPushButton, QGridLayout, QShortcut)
from PyQt5.QtGui import QImage, QPixmap, QColor, QPainter, QPen, QFont, QTransform, QKeySequence
from PyQt5.QtCore import Qt, QPoint


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(0, 0, 1280, 720)
        self.setFont(QFont('Segoe UI', 12))

        # self.canvas = QImage(self.size(), QImage.Format_ARGB32_Premultiplied)
        # self.canvas.fill(QColor(255, 0, 0, alpha=0))

        self.drawing = False
        self.currentLayer = 0
        self.lastMousePos = QPoint(0, 0)

        self.coords = QLabel(self)
        self.coords.setText('0 0')
        self.coords.setGeometry(0, 0, 200, 32)

        self.layerList = QListWidget(self)

        self.newBitmapLayer = QPushButton(self)
        self.newBitmapLayer.setText('Новый растровый слой')

        self.preview = PreviewWindow(self)
        self.preview.show()

        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(self.newBitmapLayer, 0, 0)
        self.layout.addWidget(self.layerList, 0, 1)
        self.layout.addWidget(self.preview, 0, 2)

        self.show()


class PreviewWindow(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setGeometry(10, 10, 800, 600)

        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self)
        self.view.setScene(self.scene)
        # self.view.show()

        self.scene.addPixmap(QPixmap('checkerboard.png'))

        self.zoomInShortcut = QShortcut(QKeySequence('Ctrl+='), self)
        self.zoomInShortcut.activated.connect(self.zoomIn)

        self.zoomOutShortcut = QShortcut(QKeySequence('Ctrl+-'), self)
        self.zoomOutShortcut.activated.connect(self.zoomOut)

    def zoomIn(self):
        self.view.scale(1.25, 1.25)

    def zoomOut(self):
        self.view.scale(0.8, 0.8)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())