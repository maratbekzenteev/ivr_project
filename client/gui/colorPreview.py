from PyQt5.QtWidgets import QWidget, QColorDialog, QPushButton, QGridLayout
from PyQt5.QtGui import QColor
from PyQt5.QtCore import pyqtSlot
from client.src.signals import Signals
from client.gui.coloredButton import ColoredButton


# Виджет просмотра текущего цвета с функцией его изменения с помощью QColorDialog. Набор сигналов - Signals.
# Графические элементы:
# - self.layout - QGridLayout, сетка выравнивания элементов виджета
# - self.colorButton - ColoredButton, кнопка, выступающая в роли индикатора текущего цвета
# - self.colorDialog - QColorDialog, диалог выбора цвета (отдельное окно), которого нет в палитре
# - self.chooseColorButton - QPushButton, кнопка для показа self.colorDialog
# Аттрибуты:
# - self.color - текущий цвет
class ColorPreview(QWidget):
    # Инициализация графических элементов, подключение сигналов к слотам, инициализация аттрибута
    def __init__(self):
        super().__init__()

        self.layout = QGridLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
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

    # Обработчик отображения диалога self.colorDialog, слот сигнала self.chooseColorButton.clicked
    @pyqtSlot()
    def showDialog(self):
        self.colorDialog.show()
        self.colorDialog.setCurrentColor(self.color)

    # Обработкик диалога self.colorDialog после нажатия пользователем кнопки "ОК".
    # Слот сигнала self.colorDialog.colorSelected. Обновляет цвет self.colorButton согласно новым данным,
    # сообщает сигнал valueChanged
    @pyqtSlot()
    def chooseColor(self):
        self.color = self.colorDialog.selectedColor()
        self.colorButton.setColor(self.color)

        self.signals.valueChanged.emit()

    # Функция обновления цвета извне, например, при выборе цвета пользователем через ColorPicker
    def setColor(self, color: QColor) -> None:
        self.color = color
        self.colorButton.setColor(color)
