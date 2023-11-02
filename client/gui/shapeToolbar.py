from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QSlider
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt, pyqtSlot
from client.src.signals import Signals
from client.gui.colorPreview import ColorPreview
from client.gui.widthPictogram import WidthPictogram
from client.gui.toolSelector import ToolSelector


class ShapeToolbar(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QGridLayout(self)
        self.setLayout(self.layout)

        self.signals = Signals()

        self.lineColor = QColor(0, 0, 0)
        self.lineColorPreview = ColorPreview()
        self.lineColorPreview.signals.valueChanged.connect(self.updateValues)

        self.fillColor = QColor(0, 0, 0)
        self.fillColorPreview = ColorPreview()
        self.fillColorPreview.signals.valueChanged.connect(self.updateValues)

        self.width = 1
        self.widthSlider = QSlider()
        self.widthSlider.setMinimum(1)
        self.widthSlider.setMaximum(32)
        self.widthSlider.valueChanged.connect(self.updateValues)

        self.tool = 'none'
        self.toolSelector = ToolSelector('Привязать', 'Передвинуть')
        self.toolSelector.setStates('grid', 'ofst')
        self.toolSelector.setIcons(*(['tmp_icon.png'] * 2))
        self.toolSelector.signals.valueChanged.connect(self.updateValues)

        self.shape = 'none'
        self.shapeSelector = ToolSelector('Отрезок', 'Прямоугольник', 'Эллипс')
        self.shapeSelector.setStates('line', 'rect', 'oval')
        self.shapeSelector.setIcons(*(['tmp_icon.png'] * 3))
        self.shapeSelector.signals.valueChanged.connect(self.updateValues)

        self.layout.addWidget(QLabel('Заливка'), 0, 0)
        self.layout.addWidget(QLabel('Обводка'), 0, 1)
        self.layout.addWidget(QLabel('Толщина'), 0, 2, 1, 2, Qt.AlignTop)
        self.layout.addWidget(QLabel('Переместить'), 0, 4)
        self.layout.addWidget(QLabel('Фигура'), 0, 5)
        self.layout.addWidget(self.fillColorPreview, 1, 0)
        self.layout.addWidget(self.lineColorPreview, 1, 1)
        self.layout.addWidget(self.widthSlider, 1, 2)
        self.layout.addWidget(WidthPictogram(), 1, 3)
        self.layout.addWidget(self.toolSelector, 1, 4)
        self.layout.addWidget(self.shapeSelector, 1, 5)

    @pyqtSlot()
    def updateValues(self):
        self.lineColor = self.lineColorPreview.color
        self.fillColor = self.fillColorPreview.color
        self.width = self.widthSlider.value()
        self.tool = self.toolSelector.state
        self.shape = self.shapeSelector.state

        self.signals.valueChanged.emit()

    def setState(self, lineColor: QColor, fillColor: QColor, width: int, tool: str, shape: str):
        self.lineColor = lineColor
        self.lineColorPreview.setColor(lineColor)
        self.fillColor = fillColor
        self.fillColorPreview.setColor(fillColor)
        self.tool = tool
        self.toolSelector.setState(tool)
        self.shape = shape
        self.shapeSelector.setState(shape)
        self.width = width
        # self.widthSlider.setValue(width)
