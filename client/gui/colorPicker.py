from PyQt5.QtWidgets import QWidget, QGridLayout
from PyQt5.QtGui import QColor
from PyQt5.QtCore import pyqtSlot
from client.src.signals import Signals
from client.gui.coloredButton import ColoredButton


# Виджет палитры (25 цветов в ширину, 5 цветов в высоту) для выбора цвета. Набор сигналов - Signals
# Цвета, размещенные в каждой из ячеек палитры, реализованы классом ColoredButton
# Графические элементы:
# - self.layout - QGridLayout, сетка выравнивания ColoredButton в палитре
# - Объекты класса ColoredButton, на каждый по 1 цвету
# Атрибуты:
# - self.color - QColor, текущий цвет
class ColorPicker(QWidget):
    # Инициализация атрибутов, соединение сигналов со слотами, размещение ColoredButton в ячейки сетки
    def __init__(self) -> None:
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

    # Функция для обновления цвета извне (например, когда пользователь обновил цвет через ColorPreview)
    def setColor(self, color: QColor) -> None:
        self.color = color

    # Обновление цвета при нажатии ColoredButton, слот сигнала ColoredButton.clicked.
    # Сообщает сигнал self.signals.valueChanged
    @pyqtSlot()
    def updateColor(self) -> None:
        self.color = self.sender().color
        self.signals.valueChanged.emit()
