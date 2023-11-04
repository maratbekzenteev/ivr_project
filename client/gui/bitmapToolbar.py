from PyQt5.QtWidgets import QWidget, QGridLayout, QSlider
from PyQt5.QtGui import QColor
from PyQt5.QtCore import pyqtSlot
from client.src.signals import Signals
from client.gui.colorPicker import ColorPicker
from client.gui.colorPreview import ColorPreview
from client.gui.widthPictogram import WidthPictogram
from client.gui.toolSelector import ToolSelector


# Виджет панели инструментов для работы с растровыми слоями. Набор сигналов - Signals
# Графические элементы:
# - self.layout - QGridLayout, сетка выравнивания виджетов в панели
# - self.colorPicker - ColorPicker, палитра со стандартными цветами
# - self.colorPreview - ColorPreview, индикатор текущего выбранного цвета с кнопкой выбора другого цвета (не из палитры)
# - self.widthSlider - QSlider - ползунок выбора толщины (ширины) кисти/карандаша/ручки, принимает значения от 1 до 32
# - self.toolSelector - ToolSelector, выбор текущего инструмента для работы со слоем
# Атрибуты:
# - self.color - QColor, цвет заливки, кисти, карандаша, ручки, прямоугольника, прямой, эллипса
# - self.width - int, толщина кисти, карандаша, ручки, прямоугольника, эллипса, прямой
# - self.tool - str (в будущем планируется заменить на Enum), текущий выбранный инструмент
# - - Значения (названия имеют длину до 4 симв. включительно, чтобы ускорить сравнение строк):
# - - - 'none' - инструмент не выбран
# - - - 'brsh' - кисть. След кисти идёт по траектории движения мыши с опущенной ЛКМ. Форма следа округлая (Qt.RoundCap)
# - - - 'pen' - ручка. То же, что и кисть, но с более угловатой формой следа (Qt.SquareCap)
# - - - 'penc' - карандаш. То же, что и кисть, но с более отрывистой формой следа (Qt.FlatCap)
# - - - 'ersr'
# - - - 'line' - отрезок. Соединяет отрезком точку нажания и точку отпускания ЛКМ.
# - - - 'rect' - прямоугольник. Строит прямоугольник по диагонали, заданной пользователем как отрезок, соединяющий
# - - - - точку нажатия и точку отпускания ЛКМ, со сторонами, параллельными осям координат
# - - - 'oval' - эллипс. Строит эллипс, вписанный в прямоугольник, построенный описанным выше способом
# - - - 'fill' - заливка. Меняет цвет области точек цвета точки, в которой была нажата ЛКМ. Область ограничена
# - - - - точками другого цвета
class BitmapToolbar(QWidget):
    # Инициализация интерфейса, подключение сигналов к слотам, объявление атрибутов класса
    def __init__(self) -> None:
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
        self.toolSelector = ToolSelector('Кисть', 'Ручка', 'Карандаш', 'Ластик', 'Отрезок', 'Прямоугольник', 'Эллипс', 'Заливка')
        self.toolSelector.setIcons(*(['tmp_icon.png'] * 8))
        self.toolSelector.setStates('brsh', 'pen', 'penc', 'ersr', 'line', 'rect', 'oval', 'fill')
        self.toolSelector.signals.valueChanged.connect(self.updateValues)

        self.layout.addWidget(self.colorPicker, 0, 0)
        self.layout.addWidget(self.colorPreview, 0, 1)
        self.layout.addWidget(self.widthSlider, 0, 2)
        self.layout.addWidget(WidthPictogram(), 0, 3)
        self.layout.addWidget(self.toolSelector, 0, 4)

    # Обновление состояния класса. Слот для сигналов valueChanged элементов графического интерфейса.
    # Если цвета self.colorPreview, self.colorPicker и self.color не совпадают, значит, цвет был изменен.
    # Цвет всех эл-ов меняется на самый новый, т.е. на тот, который имеет лишь 1 из 3 эл-ов.
    # Также обновляется толщина и инструмент. Сообщается сигнал valueChanged
    @pyqtSlot()
    def updateValues(self) -> None:
        if self.colorPreview.color != self.color:
            self.color = self.colorPreview.color
            self.colorPicker.setColor(self.color)
        elif self.colorPicker.color != self.color:
            self.color = self.colorPicker.color
            self.colorPreview.setColor(self.color)

        self.width = self.widthSlider.value()
        self.tool = self.toolSelector.state
        self.signals.valueChanged.emit()
