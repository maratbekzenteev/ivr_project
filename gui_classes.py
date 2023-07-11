from PyQt5.QtWidgets import (QApplication, QGraphicsScene, QGraphicsView, QTabWidget, QLabel,
                             QWidget, QListWidget, QPushButton, QGridLayout, QShortcut, QSpinBox)
from PyQt5.QtGui import QPixmap, QFont, QKeySequence
from PyQt5.QtCore import Qt, QRect


class BitmapToolbar(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QGridLayout(self)
        self.setLayout(self.layout)

        self.red = QSpinBox(self)
        self.red.setMinimum(0)
        self.red.setMaximum(255)

        self.green = QSpinBox(self)
        self.green.setMinimum(0)
        self.green.setMaximum(255)

        self.blue = QSpinBox(self)
        self.blue.setMinimum(0)
        self.blue.setMaximum(255)

        self.layout.addWidget(self.red, 0, 0)
        self.layout.addWidget(self.green, 0, 1)
        self.layout.addWidget(self.blue, 0, 2)