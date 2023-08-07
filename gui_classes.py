from PyQt5.QtWidgets import (QApplication, QGraphicsScene, QGraphicsView, QTabWidget, QLabel, QToolButton,
                             QWidget, QListWidget, QPushButton, QGridLayout, QShortcut, QSpinBox, QSlider, QColorDialog)
from PyQt5.QtGui import QPixmap, QFont, QKeySequence, QPalette, QBrush, QColor, QPainter, QPen, QIcon
from PyQt5.QtCore import Qt, QRect, pyqtSignal, QObject, QSize
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
        self.colorPreview = ColorPreview()
        self.colorPreview.signals.valueChanged.connect(self.updateValues)


        self.width = 1
        self.widthSlider = QSlider()
        self.widthSlider.setMinimum(1)
        self.widthSlider.setMaximum(32)
        self.widthSlider.valueChanged.connect(self.updateValues)

        self.tool = 'none'
        self.toolSelector = ToolSelector('Кисть', 'Ручка', 'Карандаш', 'Прямая', 'Прямоугольник', 'Эллипс', 'Заливка')
        self.toolSelector.setIcons(*(['tmp_icon.png'] * 7))
        self.toolSelector.setStates('brsh', 'pen', 'penc', 'line', 'rect', 'oval', 'fill')
        self.toolSelector.signals.valueChanged.connect(self.updateValues)

        self.layout.addWidget(self.colorPicker, 0, 0)
        self.layout.addWidget(self.colorPreview, 0, 1)
        self.layout.addWidget(self.widthSlider, 0, 2)
        self.layout.addWidget(WidthPictogram(), 0, 3)
        self.layout.addWidget(self.toolSelector, 0, 4)

    def updateValues(self):
        if self.colorPreview.color != self.color:
            self.color = self.colorPreview.color
            self.colorPicker.setColor(self.color)
        elif self.colorPicker.color != self.color:
            self.color = self.colorPicker.color
            self.colorPreview.updateState(self.color)

        self.width = self.widthSlider.value()
        self.tool = self.toolSelector.state
        self.signals.valueChanged.emit()


class ColorPicker(QWidget):
    def __init__(self):
        super().__init__()

        self.signals = Signals()

        self.layout = QGridLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.color = QColor(0, 0, 0)

        for red in range(5):
            for green in range(5):
                for blue in range(5):
                    self.layout.addWidget(
                        ColoredButton(QColor(min(255, red * 64), min(255, green * 64), min(255, blue * 64))),
                        red, green * 5 + blue
                    )
                    self.layout.itemAtPosition(red, green * 5 + blue).widget().clicked.connect(self.updateColor)

    def setColor(self, color):
        self.color = color

    def updateColor(self):
        self.color = self.sender().color
        self.signals.valueChanged.emit()


class ColoredButton(QPushButton):
    def __init__(self, color):
        super().__init__()

        self.setMinimumSize(8, 8)
        self.setMaximumSize(128, 128)

        self.color = color

        palette = self.palette()
        palette.setColor(QPalette.Button, color)
        self.setFlat(True)
        self.setAutoFillBackground(True)
        self.setPalette(palette)
        self.repaint()

    def updateState(self, color):
        palette = self.palette()
        palette.setColor(QPalette.Button, color)
        self.setPalette(palette)
        self.repaint()


class ColorPreview(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QGridLayout(self)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)

        self.signals = Signals()

        self.color = QColor(0, 0, 0)
        self.colorButton = ColoredButton(QColor(0, 0, 0))

        self.colorDialog = QColorDialog()
        self.colorDialog.setOption(QColorDialog.ShowAlphaChannel, on=True)
        self.colorDialog.colorSelected.connect(self.chooseColor)

        self.chooseColorButton = QPushButton('Другой цвет')
        self.chooseColorButton.clicked.connect(self.showDialog)

        self.layout.addWidget(self.colorButton, 0, 0)
        self.layout.addWidget(self.chooseColorButton, 1, 0)

    def showDialog(self):
        self.colorDialog.show()
        self.colorDialog.setCurrentColor(self.color)

    def chooseColor(self):
        self.color = self.colorDialog.selectedColor()
        self.colorButton.updateState(self.color)

        self.signals.valueChanged.emit()

    def updateState(self, color):
        self.color = color
        self.colorButton.updateState(color)


class WidthPictogram(QWidget):
    def __init__(self):
        super().__init__()
        self.setMaximumSize(32, 256)
        self.setMinimumSize(16, 32)

    def paintEvent(self, event):
        qp = QPainter(self)
        height = self.geometry().height()
        width = self.geometry().width()
        for i in range(16):
            qp.setPen(QPen(QColor(0, 0, 0), 16 - i, Qt.SolidLine, Qt.RoundCap, Qt.BevelJoin))
            qp.drawPoint(width // 2, i * height // 16)


class ToolSelector(QWidget):
    def __init__(self, *button_names):
        super().__init__()

        self.signals = Signals()

        self.layout = QGridLayout(self)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)

        self.buttonToState = dict()
        self.state = 'none'

        for i in range(len(button_names)):
            self.layout.addWidget(QToolButton(), 0, i)
            self.layout.itemAtPosition(0, i).widget().setText(button_names[i])
            self.layout.itemAtPosition(0, i).widget().clicked.connect(self.updateState)
            self.layout.itemAtPosition(0, i).widget().setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            self.layout.itemAtPosition(0, i).widget().setAutoRaise(True)
            self.layout.itemAtPosition(0, i).widget().setCheckable(True)
            self.layout.itemAtPosition(0, i).widget().setIconSize(QSize(96, 96))

    def setStates(self, *states):
        for i in range(len(states)):
            self.buttonToState[self.layout.itemAtPosition(0, i).widget().text()] = states[i]

    def setIcons(self, *icons):
        for i in range(len(icons)):
            self.layout.itemAtPosition(0, i).widget().setIcon(QIcon('tmp_icon.png'))

    def updateState(self):
        if self.sender().isChecked():
            self.state = self.buttonToState[self.sender().text()]

            for i in range(len(self.buttonToState)):
                self.layout.itemAtPosition(0, i).widget().setChecked(False)
            self.sender().setChecked(True)

        else:
            self.state = 'none'

        self.signals.valueChanged.emit()