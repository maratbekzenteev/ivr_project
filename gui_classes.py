from PyQt5.QtWidgets import (QApplication, QGraphicsScene, QGraphicsView, QTabWidget, QLabel,
                             QWidget, QListWidget, QPushButton, QGridLayout, QShortcut, QSpinBox, QSlider)
from PyQt5.QtGui import QPixmap, QFont, QKeySequence, QPalette, QBrush, QColor
from PyQt5.QtCore import Qt, QRect, pyqtSignal, QObject
from colorsys import hsv_to_rgb, rgb_to_hsv


class Signals(QObject):
    valueChanged = pyqtSignal()


class BitmapToolbar(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QGridLayout(self)
        self.setLayout(self.layout)

        self.signals = Signals()

        self.color = QColor(0, 0, 0)
        self.colorPicker = ColorPicker()
        self.colorPicker.signals.valueChanged.connect(self.updateValues)

        self.layout.addWidget(self.colorPicker, 0, 0)

    def updateValues(self):
        self.color = self.colorPicker.color
        self.signals.valueChanged.emit()


class ColorPicker(QWidget):
    def __init__(self):
        super().__init__()

        self.signals = Signals()

        self.layout = QGridLayout(self)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)

        self.color = QColor(0, 0, 0)

        for red in range(5):
            for green in range(5):
                for blue in range(5):
                    self.layout.addWidget(
                        ColoredButton(QColor(min(255, red * 64), min(255, green * 64), min(255, blue * 64))),
                        red, green * 4 + blue
                    )
                    self.layout.itemAtPosition(red, green * 4 + blue).widget().clicked.connect(self.updateColor)

    def updateColor(self):
        self.color = self.sender().color
        self.signals.valueChanged.emit()


class ColoredButton(QPushButton):
    def __init__(self, color):
        super().__init__()

        self.color = color

        palette = self.palette()
        palette.setColor(QPalette.Button, color)
        self.setFlat(True)
        self.setAutoFillBackground(True)
        self.setPalette(palette)
        self.repaint()
