from PyQt5.QtWidgets import QWidget, QSpinBox, QFontComboBox, QToolButton, QGridLayout
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtCore import pyqtSlot, Qt
from client.gui.colorPreview import ColorPreview
from client.gui.toolSelector import ToolSelector
from client.src.signals import Signals


# Виджет панели инструментов для манипуляций с текстовым слоем. Набор сигналов - Signals.
# Графические элементы:
# - self.layout - QGridLayout, сетка выравнивания всех графических элементов внутри виджета
# - self.colorPreview - ColorPreview, отвечает за предпросмотр и изменение цвета выделенных и новых символов
# - self.fontComboBox - QFontComboBox, отвечает за выбор шрифта выделенных и новых символов
# - self.sizeSpinBox - QSpinBox, отвечает за размер шрифта выделенных и новых символов
# - self.fontWeightButton - QToolButton, отвечает за жирность выделенных и новых символов
# - self.italicButton - QToolButton, отвечает за курсивность выделенных и новых символов
# - self.underlineButton - QToolButton, отвечает за подчёркнутось выделенных и новых символов
# - alignmentSelector - ToolSelector, позволяет выбрать выравниваение всей плашки текста внутри прямоугольника сетки.
# - - Каждое состояние соответствует определенному значению self.alignment:
# - - - 'none' - Qt.AlignLeft
# - - - 'left' - Qt.AlignLeft
# - - - 'cntr' - Qt.AlignCenter
# - - - 'rght- - Qt.AlignRight
# - - - 'fill' - Qt.AlignJustify
# Атрибуты:
# - self.color - QColor, цвет выделенных и новых символов
# - self.font - str, шрифт выделенных и новых символов
# - self.size - int, размер шрифта выделенных и новых символов, принимает значения от 1 до 256
# - self.fontWeight - QFont::Weight, задаёт жирность выделенных и новых символов,
# - - принимает значения:
# - - - QFont.Normal - нежирный
# - - - QFont.DemiBold - полужирный
# - self.italic - bool, задаёт курсивность выделенных и новых символов
# - self.underline - bool, задаёт подчёркнутость выделенных и новых символов
# - self.alignment - Qt::AlignmentFlag, задаёт выравнивание текста, принимает значения:
# - - Qt.AlignLeft - выравнивание по левому краю
# - - Qt.AlignCenter - выравнивание по ценрту
# - - Qt.AlignRight - выравниваение по правому краю
# - - Qt.AlignJustify - выравнивание по всей ширине
# где "новые символы" - символы, ещё не добавленные, появляющиеся на текущей позиции курсора
class TextToolbar(QWidget):
    # Инициализация графических элементов, подключение сигналов к слотам, инициализация атрибутов
    def __init__(self) -> None:
        super().__init__()

        self.layout = QGridLayout(self)
        self.setLayout(self.layout)

        self.signals = Signals()

        self.color = QColor(0, 0, 0)
        self.colorPreview = ColorPreview()
        self.colorPreview.signals.valueChanged.connect(self.updateValues)

        self.font = 'Verdana'
        self.fontComboBox = QFontComboBox()
        self.fontComboBox.setFont(QFont('Verdana'))
        self.fontComboBox.currentFontChanged.connect(self.updateValues)

        self.sizeSpinBox = QSpinBox()
        self.sizeSpinBox.setMinimum(1)
        self.sizeSpinBox.setMaximum(256)
        self.sizeSpinBox.setValue(32)
        self.size = 32
        self.sizeSpinBox.valueChanged.connect(self.updateValues)

        self.fontWeight = QFont.Normal
        self.fontWeightButton = QToolButton()
        self.fontWeightButton.setText('Ж')
        self.fontWeightButton.setAutoRaise(True)
        self.fontWeightButton.setCheckable(True)
        self.fontWeightButton.clicked.connect(self.updateValues)

        self.italic = False
        self.italicButton = QToolButton()
        self.italicButton.setText('К')
        self.italicButton.setAutoRaise(True)
        self.italicButton.setCheckable(True)
        self.italicButton.clicked.connect(self.updateValues)

        self.underline = False
        self.underlineButton = QToolButton()
        self.underlineButton.setText('П')
        self.underlineButton.setAutoRaise(True)
        self.underlineButton.setCheckable(True)
        self.underlineButton.clicked.connect(self.updateValues)

        self.alignment = Qt.AlignLeft
        self.stringToQtAlignment = {
            'none': Qt.AlignLeft,
            'left': Qt.AlignLeft,
            'cntr': Qt.AlignCenter,
            'rght': Qt.AlignRight,
            'fill': Qt.AlignJustify
        }
        self.alignmentSelector = ToolSelector('Слева', 'По центру', 'Справа', 'Заполнить')
        self.alignmentSelector.setStates('left', 'cntr', 'rght', 'fill')
        self.alignmentSelector.signals.valueChanged.connect(self.updateValues)

        self.layout.addWidget(self.fontComboBox, 0, 0)
        self.layout.addWidget(self.sizeSpinBox, 0, 1)
        self.layout.addWidget(self.fontWeightButton, 0, 2)
        self.layout.addWidget(self.italicButton, 0, 3)
        self.layout.addWidget(self.underlineButton, 0, 4)
        self.layout.addWidget(self.colorPreview, 0, 5)
        self.layout.addWidget(self.alignmentSelector, 0, 6)

    # Обновление атрибутов "изнутри". Слот сигналов self.colorPreview.signals.valueChanged,
    # self.fontComboBox.currentFontChanged, self.sizeSpinBox.valueChanged, self.fontWeightButton.clicked,
    # self.italicButton.clicked, self.underlineButton.clicked. Сообщает сигнал signals.valueChanged
    @pyqtSlot()
    def updateValues(self) -> None:
        self.color = self.colorPreview.color
        self.font = self.fontComboBox.currentFont()
        self.size = self.sizeSpinBox.value()
        self.fontWeight = QFont.Weight.DemiBold if self.fontWeightButton.isChecked() else QFont.Weight.Normal
        self.italic = self.italicButton.isChecked()
        self.underline = self.underlineButton.isChecked()
        self.alignment = self.stringToQtAlignment[self.alignmentSelector.state]

        self.signals.valueChanged.emit()

    # Обновление атрибутов (и графических элементов) "извне" (из родительского класса). Вызывается при смене позиции
    # курсора и при смене выделенного текстового слоя
    def setState(self, color: QColor, font: str, size: int, fontWeight: QFont.Weight, italic: bool, underline: bool,
                 alignment: Qt.AlignmentFlag) -> None:
        self.color = color
        self.colorPreview.setColor(color)
        self.font = font
        self.fontComboBox.setFont(QFont(font))
        self.fontWeight = fontWeight
        self.fontWeightButton.setChecked(fontWeight == QFont.Weight.DemiBold)
        self.italic = italic
        self.italicButton.setChecked(italic)
        self.underline = underline
        self.underlineButton.setChecked(underline)
        self.size = size
        self.alignment = alignment
        for i in self.stringToQtAlignment:
            if self.stringToQtAlignment[i] == alignment:
                self.alignmentSelector.setState(i)
                break
