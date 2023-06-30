import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QGraphicsScene, QGraphicsView, QGraphicsItem,
                             QDockWidget, QWidget, QListWidget, QPushButton, QGridLayout, QShortcut)
from PyQt5.QtGui import QImage, QPixmap, QColor, QPainter, QPen, QFont, QTransform, QKeySequence
from PyQt5.QtCore import Qt, QPoint, QRect


class Window(QWidget):
    def __init__(self):
        super().__init__()
        # self.setFont(QFont('Segoe UI', 12))

        layout = QGridLayout()
        self.setLayout(layout)

        # self.canvas = QImage(self.size(), QImage.Format_ARGB32_Premultiplied)
        # self.canvas.fill(QColor(255, 0, 0, alpha=0))

        self.currentLayer = 0
        self.lastMousePos = QPoint(0, 0)

        layout.addWidget(QPushButton(self), 0, 0)
        layout.itemAtPosition(0, 0).widget().setText('0')
        layout.addWidget(QPushButton('0'), 0, 1)
        layout.addWidget(PreviewWindow(self), 1, 0, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(QPushButton('3'), 1, 1)
        layout.itemAtPosition(1, 1).widget().setText('3')

        self.show()


class PreviewWindow(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setMinimumSize(800, 600)

        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self)
        self.view.setScene(self.scene)
        self.view.setMinimumSize(800, 600)
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