from PyQt5.QtWidgets import QWidget, QGridLayout, QToolButton
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize, Qt, pyqtSlot
from signals import Signals


# Виджет выбора инструмента. Отличается от обычной таблицы с кнопками тем, что кнопка отпускается сама
# при нажатии другой кнопки, но при бездействии остается нажатой, а при повторном нажатии отпускается.
# Набор сигналов - Signals
# Графические элементы:
# - self.layout - QGridLayout, сетка для выравнивания QToolButton
# - QToolButton, размещенные в сетке
# Аттрибуты:
# - self.buttonToState - dict(str, str), ключи - тексты на кнопках, значения - соответствующие им значения self.state
# - self.state - str, текущее состояние, соответствующее выбранному инструменту ('none', если инструмент не выбран)
class ToolSelector(QWidget):
    # Инициализация графических элементов, соединение сигналов и слотов, определение названий и кол-ва кнопок
    def __init__(self, *button_names: str) -> None:
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

    # Определение словаря self.buttonToState, в аргументах передаются названия состояний,
    # соответствующих каждой из кнопок в порядке слева направо. К-во состояний не должно превышать к-во кнопок,
    # определенных при инициализации
    def setStates(self, *states: str) -> None:
        for i in range(len(states)):
            self.buttonToState[self.layout.itemAtPosition(0, i).widget().text()] = states[i]

    # Присвоение кнопкам иконок, названия которых перечислены в аргументах в порядке следованя кнопок слева направо
    def setIcons(self, *icons):
        for i in range(len(icons)):
            self.layout.itemAtPosition(0, i).widget().setIcon(QIcon('tmp_icon.png'))

    # Обновление состояния при нажатии одной из кнопок. Слот сигнала self.layout.itemAtPosition(0, i).widget().clicked
    # Сообщает сигнал valueChanged
    @pyqtSlot()
    def updateState(self):
        if self.sender().isChecked():
            self.state = self.buttonToState[self.sender().text()]

            for i in range(len(self.buttonToState)):
                self.layout.itemAtPosition(0, i).widget().setChecked(False)
            self.sender().setChecked(True)

        else:
            self.state = 'none'

        self.signals.valueChanged.emit()
