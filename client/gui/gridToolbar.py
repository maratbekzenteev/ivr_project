from PyQt5.QtWidgets import (QWidget, QGridLayout, QListWidget, QSpinBox, QRadioButton,
                             QPushButton, QButtonGroup, QLabel, QAbstractButton)
from PyQt5.QtCore import Qt, pyqtSlot
from client.src.signals import GridSignals


# Виджет панели инструментов для манипуляции с сеткой. Набор сигналов - GridSignals.
# Графические элементы:
# - self.layout - QGridLayout, сетка выравнивания элементов панели
# - self.vList - QListWidget, список вертикальных линий сетки
# - self.vSpinBox - QSpinBox, поле выбора отступа добавляемой вертикальной линии от левого края в процентах/пикселях
# - self.vPercentButton - QRadioButton, кнопка выбора процентов для задания отступа добавляемой вертикальной линии
# - self.vPixelButton - QRadioButton, кнопка выбора пикселей для задания отступа добавляемой вертикальной линии сетки
# - self.vAddButton - QPushButton, кнопка добавления вертикальной линии сетки
# - self.vDeleteButton - QPushButton, кнопка удаления выделенной в self.vList линии сетки
# - self.vButtons - QButtonGroup, группа, объединяющая self.vPercentButton и vPixelButton
# - self.hList - QListWidget, список горизонтальных линий сетки
# - self.hSpinBox - QSpinBox, поле выбора отступа добавляемой горизонтальной линии от верхнего края в процентах/пикселях
# - self.hPercentButton - QRadioButton, кнопка выбора процентов для задания отступа добавляемой горизонтальной линии
# - self.hPixelButton - QRadioButton, кнопка выбора пикселей для задания отступа добавляемой горизонтальной линии сетки
# - self.hAddButton - QPushButton, кнопка добавления горизонтальной линии сетки
# - self.hDeleteButton - QPushButton, кнопка удаления выделенной в self.hList линии сетки
# - self.hButtons - QButtonGroup, группа, объединяющая self.hPercentButton и hPixelButton
# Атрибуты:
# - self.resolution - tuple(int, int), разрешение текущего проекта
# - self.currentVIndentType - int, задает тип задания отступа добавляемой вертикальной линии сетки, принимает значения:
# - - -1 - значение не выбрано пользователем
# - - 0 - абсолютное задание (в пикселях)
# - - 1 - относительное задание (в процентах)
# - self.currentHIndentType - int, аналогичен предыдущему, но для горизонтальных линий сетки
class GridToolbar(QWidget):
    # Инициализация графических элементов и атрибутов виджета
    def __init__(self, resolution: tuple):
        super().__init__()

        self.layout = QGridLayout(self)
        self.setLayout(self.layout)

        self.signals = GridSignals()

        self.resolution = resolution
        self.currentVIndentType = -1
        self.currentHIndentType = -1

        self.vList = QListWidget()

        self.vSpinBox = QSpinBox()
        self.vSpinBox.setMinimum(0)
        self.vSpinBox.setMaximum(0)

        self.vPercentButton = QRadioButton('Процентов')
        self.vPixelButton = QRadioButton('Пикселей')

        self.vAddButton = QPushButton('Добавить')
        self.vAddButton.clicked.connect(self.addVLine)

        self.vDeleteButton = QPushButton('Удалить')
        self.vDeleteButton.clicked.connect(self.deleteVLine)

        self.vButtons = QButtonGroup()
        self.vButtons.addButton(self.vPixelButton)
        self.vButtons.addButton(self.vPercentButton)
        self.vButtons.buttonClicked.connect(self.updateVIndentType)

        self.layout.addWidget(QLabel('Вертикальные прямые'), 0, 0, 1, 2, Qt.AlignLeft)
        self.layout.addWidget(self.vList, 1, 0, 5, 1, Qt.AlignLeft)
        self.layout.addWidget(self.vSpinBox, 1, 1)
        self.layout.addWidget(self.vPercentButton, 2, 1)
        self.layout.addWidget(self.vPixelButton, 3, 1)
        self.layout.addWidget(self.vAddButton, 4, 1)
        self.layout.addWidget(self.vDeleteButton, 5, 1)

        self.hList = QListWidget()

        self.hSpinBox = QSpinBox()
        self.hSpinBox.setMinimum(0)
        self.hSpinBox.setMaximum(0)

        self.hPercentButton = QRadioButton('Процентов')
        self.hPixelButton = QRadioButton('Пикселей')

        self.hAddButton = QPushButton('Добавить')
        self.hAddButton.clicked.connect(self.addHLine)

        self.hDeleteButton = QPushButton('Удалить')
        self.hDeleteButton.clicked.connect(self.deleteHLine)

        self.hButtons = QButtonGroup()
        self.hButtons.addButton(self.hPixelButton)
        self.hButtons.addButton(self.hPercentButton)
        self.hButtons.buttonClicked.connect(self.updateHIndentType)

        self.layout.addWidget(QLabel('Горизонтальные прямые'), 0, 2, 1, 2, Qt.AlignLeft)
        self.layout.addWidget(self.hList, 1, 2, 5, 1, Qt.AlignLeft)
        self.layout.addWidget(self.hSpinBox, 1, 3)
        self.layout.addWidget(self.hPercentButton, 2, 3)
        self.layout.addWidget(self.hPixelButton, 3, 3)
        self.layout.addWidget(self.hAddButton, 4, 3)
        self.layout.addWidget(self.hDeleteButton, 5, 3)

    # Обновление типа отступа добавляемой вертикальной линии сетки. Слот сигнала self.vButtons.buttonClicked
    @pyqtSlot(QAbstractButton)
    def updateVIndentType(self, button: QRadioButton) -> None:
        if button.text() == 'Процентов':
            self.vSpinBox.setMaximum(100)
            self.currentVIndentType = 1
        else:
            self.vSpinBox.setMaximum(self.resolution[0])
            self.currentVIndentType = 0

    # Обновление типа отступа добавляемой горизонтальной линии сетки. Слот сигнала self.hButtons.buttonClicked
    @pyqtSlot(QAbstractButton)
    def updateHIndentType(self, button: QRadioButton) -> None:
        if button.text() == 'Процентов':
            self.hSpinBox.setMaximum(100)
            self.currentHIndentType = 1
        else:
            self.hSpinBox.setMaximum(self.resolution[0])
            self.currentHIndentType = 0

    # Добавление вертикальной линии сетки. Слот сигнала self.vAddButton.clicked. Сообщает сигнал signals.added
    @pyqtSlot()
    def addVLine(self) -> None:
        if self.currentVIndentType == -1:
            return
        elif self.currentVIndentType == 1:
            self.vList.addItem(f"{self.vSpinBox.value()} %")
        else:
            self.vList.addItem(f"{self.vSpinBox.value()} px")

        self.sortV()
        self.signals.added.emit(1, self.currentVIndentType, self.vSpinBox.value())

    # Добавление горизонтальной линии сетки. Слот сигнала self.hAddButton.clicked. Сообщает сигнал signals.added
    @pyqtSlot()
    def addHLine(self) -> None:
        if self.currentHIndentType == -1:
            return
        elif self.currentHIndentType == 1:
            self.hList.addItem(f"{self.hSpinBox.value()} %")
        else:
            self.hList.addItem(f"{self.hSpinBox.value()} px")

        self.sortH()
        self.signals.added.emit(0, self.currentHIndentType, self.hSpinBox.value())

    # Сортировка списка вертикальных линий сетки. Вызывается после добавления новой линии и изменения разрешения
    def sortV(self) -> None:
        lines = [self.vList.item(i).text() for i in range(self.vList.count())]
        self.vList.clear()
        lines.sort(key=lambda string:
        int(string.split()[0]) if string[-1] == 'x' else self.resolution[0] / 100 * int(string.split()[0]))
        for i in lines:
            self.vList.addItem(i)

    # Сортировка списка горизонтальных линий сетки. Вызывается после добавления новой линии и изменения разрешения
    def sortH(self) -> None:
        lines = [self.hList.item(i).text() for i in range(self.hList.count())]
        self.hList.clear()
        lines.sort(key=lambda string:
        int(string.split()[0]) if string[-1] == 'x' else self.resolution[1] / 100 * int(string.split()[0]))
        for i in lines:
            self.hList.addItem(i)

    # Удаление вертикальной линии сетки. Слот сигнала self.vDeleteButton.clicked. Сообщает сигнал signals.deleted
    @pyqtSlot()
    def deleteVLine(self) -> None:
        if self.vList.currentRow() == -1:
            return

        selectedItemText = self.vList.currentItem().text()
        self.vList.takeItem(self.vList.currentRow())
        self.signals.deleted.emit(1, 0 if selectedItemText[-1] == 'x' else 1, int(selectedItemText.split()[0]))

    # Удаление горизонтальной линии сетки. Слот сигнала self.hDeleteButton.clicked. Сообщает сигнал signals.deleted
    @pyqtSlot()
    def deleteHLine(self) -> None:
        if self.hList.currentRow() == -1:
            return

        selectedItemText = self.hList.currentItem().text()
        self.hList.takeItem(self.hList.currentRow())
        self.signals.deleted.emit(0, 0 if selectedItemText[-1] == 'x' else 1, int(selectedItemText.split()[0]))
