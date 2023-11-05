from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QSlider
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt, pyqtSlot
from client.src.signals import Signals
from client.gui.colorPreview import ColorPreview
from client.gui.widthPictogram import WidthPictogram
from client.gui.toolSelector import ToolSelector


# Виджет панели инструментов для манипуляций с фигурным слоем. Набор сигналов - Signals.
# Графические элементы:
# - self.layout - QGridLayout, сетка выравнивания всех графических элементов внутри виджета
# - self.lineColorPreview - ColorPreview, отвечает за предпросмотр и изменение цвета обводки фигуры
# - self.fillColorPreview - ColorPreview, отвечает за предпросмотр и изменение цвета заливки фигуры
# - self.widthSlider - QSlider, отвечает за изменение толщины обводки
# - self.toolSelector - ToolSelector, позволяет выбрать текущий метод работы с текущим фигурным слоем. Состояния:
# - - 'none' - инструмент не выбран
# - - 'grid' - фигура переподвязывается по сетке
# - - 'ofst' - задается отступ - "оффсет" - в пикселях от точки, где фигура должна лежать идеально по сетке
# - self.shapeSelector - ToolSelector, позволяет выбрать фигуру, задаваемую слоем. Состояния:
# - - 'none' - фигура не выбрана, на слое не отображается ничего
# - - 'line' - отрезок между двумя точками пересечения линий сетки, заданными пользователем (см. ../src/shapeLayer.py)
# - - 'rect' - прямоугольник со сторонами, параллельными линиям сетки, две из точек которого заданы пользователем
# - - - (см. ../src/shapeLayer.py)
# - - 'oval' - овал, лежащий в прямоугольнике, метод построения которого описан выше
# Атрибуты:
# - self.lineColor - QColor, цвет обводки фигуры
# - self.fillColor - QColor, цвет заливки фигуры
# - self.width - int, толщина обводки. Принимает значения от 0 до 32
# - self.tool - str, инструмент изменения слоя (для состояний см. self.toolSelector)
# - self.shape - str, тип фигуры (для состояний см. self.shapeSelector)
class ShapeToolbar(QWidget):
    # Инициализация графических элементов, подключение сигналов к слотам, инициализация атрибутов
    def __init__(self) -> None:
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
        self.widthSlider.setMinimum(0)
        self.widthSlider.setMaximum(32)
        self.widthSlider.valueChanged.connect(self.updateValues)

        self.tool = 'none'
        self.toolSelector = ToolSelector('Привязать к сетке', 'Передвинуть')
        self.toolSelector.setStates('grid', 'ofst')
        self.toolSelector.setIcons('../static/grid2.png', '../static/offset.png')
        self.toolSelector.signals.valueChanged.connect(self.updateValues)

        self.shape = 'none'
        self.shapeSelector = ToolSelector('Отрезок', 'Прямоугольник', 'Эллипс')
        self.shapeSelector.setStates('line', 'rect', 'oval')
        self.shapeSelector.setIcons('../static/line.png', '../static/rect.png', '../static/oval.png')
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

    # Слот сигналов self.lineColorPreview.signals.valueChanged, self.fillColorPreview.signals.valueChanged,
    # self.widthSlider.valueChanged. Обновляет атрибуты класса, сообщает сигнал signals.valueChanged
    @pyqtSlot()
    def updateValues(self) -> None:
        self.lineColor = self.lineColorPreview.color
        self.fillColor = self.fillColorPreview.color
        self.width = self.widthSlider.value()
        self.tool = self.toolSelector.state
        self.shape = self.shapeSelector.state

        self.signals.valueChanged.emit()

    # Функция задания атрибутов класса извне. Вызывается при повторном выделении фигурного слоя, в таком случае
    # панель инструментов подстраивает свои значения под значения слоя
    def setState(self, lineColor: QColor, fillColor: QColor, width: int, tool: str, shape: str) -> None:
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
