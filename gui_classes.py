from PyQt5.QtWidgets import (QApplication, QGraphicsScene, QGraphicsView, QTabWidget, QLabel, QToolButton, QVBoxLayout,
                             QWidget, QListWidget, QPushButton, QGridLayout, QShortcut, QSpinBox, QSlider, QColorDialog,
                             QLineEdit)
from PyQt5.QtGui import QPixmap, QFont, QKeySequence, QPalette, QBrush, QColor, QPainter, QPen, QIcon
from PyQt5.QtCore import Qt, QRect, pyqtSignal, QObject, QSize
from colorsys import hsv_to_rgb, rgb_to_hsv


class Signals(QObject):
    valueChanged = pyqtSignal()
    activated = pyqtSignal(int)
    deactivated = pyqtSignal(int)
    shown = pyqtSignal(int)
    hidden = pyqtSignal(int)


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


class LayerToolbar(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QGridLayout(self)
        self.setLayout(self.layout)

        self.signals = Signals()

        self.newBitmapLayerButton = QToolButton()
        self.newBitmapLayerButton.setText('Новый растровый слой')
        self.newBitmapLayerButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.newBitmapLayerButton.setAutoRaise(True)
        self.newBitmapLayerButton.setIconSize(QSize(64, 64))
        self.newBitmapLayerButton.setIcon(QIcon('tmp_icon.png'))

        self.newShapeLayerButton = QToolButton()
        self.newShapeLayerButton.setText('Новый фигурный слой')
        self.newShapeLayerButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.newShapeLayerButton.setAutoRaise(True)
        self.newShapeLayerButton.setIconSize(QSize(64, 64))
        self.newShapeLayerButton.setIcon(QIcon('tmp_icon.png'))

        self.layout.addWidget(self.newBitmapLayerButton, 0, 0, alignment=Qt.AlignLeft)
        self.layout.addWidget(self.newShapeLayerButton, 1, 0, alignment=Qt.AlignLeft)


class LayerListItem(QWidget):
    def __init__(self, name, type, z, index):
        super().__init__()

        self.layout = QGridLayout(self)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)

        self.signals = Signals()

        self.z = z
        self.index = index
        self.visible = True
        self.active = False

        self.activateButton = QPushButton('⌘')
        self.activateButton.clicked.connect(self.activate)

        self.nameField = QLineEdit(name)

        self.upButton = QPushButton('Выше')

        self.downButton = QPushButton('Ниже')

        self.hideButton = QPushButton('Глаз')
        self.hideButton.clicked.connect(self.changeVisibility)

        self.layout.addWidget(self.activateButton, 0, 0, 2, 1, Qt.AlignLeft)
        self.layout.addWidget(self.nameField, 0, 1, 1, 3, Qt.AlignCenter)
        self.layout.addWidget(self.upButton, 1, 1)
        self.layout.addWidget(self.downButton, 1, 2)
        self.layout.addWidget(self.hideButton, 1, 3)

        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setBrush(QPalette.Window, QBrush(QColor(0, 0, 0, alpha=0), Qt.SolidPattern))
        self.setPalette(palette)

    def updatePalette(self):
        palette = self.palette()
        palette.setBrush(QPalette.Window, QBrush(QColor(
            0, 0, 255, alpha=64) if self.active else QColor(0, 0, 0, alpha=0), Qt.SolidPattern))
        palette.setBrush(QPalette.Text, QBrush(QColor(
            0, 0, 0) if self.visible else QColor(0, 0, 0, alpha=128), Qt.SolidPattern))
        self.setPalette(palette)

    def activate(self):
        if self.active:
            self.signals.deactivated.emit(self.index)
            self.active = False
        else:
            self.signals.activated.emit(self.index)
            self.active = True

        self.updatePalette()

    def changeVisibility(self):
        if self.visible:
            self.signals.hidden.emit(self.index)
            self.visible = False
        else:
            self.signals.shown.emit(self.index)
            self.visible = True

        self.updatePalette()


class LayerList(QWidget):
    def __init__(self, parent):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setDirection(QVBoxLayout.BottomToTop)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)

        self.signals = Signals()

        self.highestZ = 0
        self.layerCount = 0

        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setBrush(QPalette.Window, QBrush(QColor(255, 255, 255), Qt.SolidPattern))
        self.setPalette(palette)

    def newBitmapLayer(self):
        self.layerCount += 1
        self.layout.addWidget(LayerListItem(
            'Растровый слой ' + str(self.highestZ + 1), 'bmp', self.highestZ, self.highestZ))
        self.layout.itemAt(self.layerCount - 1).widget().signals.activated.connect(self.activateLayer)
        self.layout.itemAt(self.layerCount - 1).widget().signals.deactivated.connect(self.deactivateLayer)
        self.layout.itemAt(self.layerCount - 1).widget().signals.shown.connect(self.showLayer)
        self.layout.itemAt(self.layerCount - 1).widget().signals.hidden.connect(self.hideLayer)
        self.highestZ += 1

    def activateLayer(self, index):
        for i in range(self.layerCount):
            self.layout.itemAt(i).widget().active = False
            self.layout.itemAt(i).widget().updatePalette()

        self.signals.activated.emit(index)

    def deactivateLayer(self, index):
        for i in range(self.layerCount):
            self.layout.itemAt(i).widget().active = False
            self.layout.itemAt(i).widget().updatePalette()

        self.signals.deactivated.emit(index)

    def showLayer(self, index):
        self.signals.shown.emit(index)

    def hideLayer(self, index):
        self.signals.hidden.emit(index)
