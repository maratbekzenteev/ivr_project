from PyQt5.QtWidgets import QWidget, QGridLayout, QLineEdit, QPushButton
from PyQt5.QtGui import QPalette, QBrush, QColor
from PyQt5.QtCore import Qt, pyqtSlot
from client.src.signals import LayerSignals


# Виджет отображения слоя в списке слоев. Помимо прочего позволяет сделать слой текущим (активировать),
# подвинуть выше/ниже относительно других слоев, скрыть/показать слой. Необходим для размещения в LayerList.
# Набор сигналов - LayerSignals
# Графические элементы:
# - self.layout - QGridLayout, сетка для выравнивания графических элементов виджета
# - self.activateButton - QPushButton, кнопка активации слоя. Повторное нажатие деактивирует слой,
# - - так что ни один слой не выделен
# - self.nameField - QLineEdit, изменяемое название слоя.
# - - Программой не используется, лишь сохраняется в файл проекта, необходимо для удобства пользователя
# - self.upButton - QPushButton, кнопка перемещения слоя на уровень выше. Если слой уже выше всех, ничего не происходит
# - self.downButton - QPushButton, кнопка перемещения слоя на уровень ниже. Если слой ниже всех, ничего не происходит
# - self.hideButton - QPushButton, кнопка скрытия/показа слоя
# - self.deleteButton - QPushButton, кнопка удаления слоя
# Атрибуты:
# - self.z - int, высота слоя, т.е. положение по оси аппликат. Определяет отображение слоя над/под другими слоями.
# - - Чем больше self.z, тем "ближе к экрану" слой
# - self.index - int, индекс слоя в индексации Window.currentLayer, т.е. индекс слоя в self.index на 1 меньше
# - - индекса в Window.scene
# - self.type - str, тип слоя (растровый, фигурный, ...). Принимает значения:
# - - 'bmp' - растровый ("холст")
# - - 'img' - картинка
# - - 'shp' - фигурный
# - - 'txt' - текстовый
# - - 'stl' - статический
# - self.visible - bool, True - слой отображается (видим), False - слой скрыт
# - self.active - bool, True - слой активен (его можно редактировать, он текущий), False - слой деактивирован
class LayerListItem(QWidget):
    # Инициализация графических элементов, подключение сигналов к слотам, инициализация атрибутов
    def __init__(self, name: str, type: str, z: int, index: int, static=False) -> None:
        super().__init__()

        self.layout = QGridLayout(self)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)
        self.setMaximumWidth(240)

        self.signals = LayerSignals()

        self.z = z
        self.index = index
        self.type = type
        self.visible = True
        self.active = False

        self.nameField = QLineEdit(name)

        self.activateButton = QPushButton('')
        self.activateButton.clicked.connect(self.activate)

        self.upButton = QPushButton('')
        self.upButton.clicked.connect(self.moveUp)

        self.downButton = QPushButton('')
        self.downButton.clicked.connect(self.moveDown)

        self.hideButton = QPushButton('')
        self.hideButton.clicked.connect(self.changeVisibility)

        self.deleteButton = QPushButton('')
        self.deleteButton.clicked.connect(self.delete)

        if static:
            self.nameField.setDisabled(True)

            self.upButton.hide()
            self.downButton.hide()
            self.activateButton.hide()
            self.deleteButton.hide()

        self.layout.addWidget(self.activateButton, 0, 0, 2, 1, Qt.AlignLeft)
        self.layout.addWidget(self.nameField, 0, 1, 1, 4, Qt.AlignCenter)
        self.layout.addWidget(self.upButton, 1, 1)
        self.layout.addWidget(self.downButton, 1, 2)
        self.layout.addWidget(self.hideButton, 1, 3)
        self.layout.addWidget(self.deleteButton, 1, 4)

        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setBrush(QPalette.Window, QBrush(QColor(0, 0, 0, alpha=0), Qt.SolidPattern))
        self.setPalette(palette)

    # Функция обновления внешнего вида виджета (например, при активации). Фон активного виджета светло-синий,
    # неактивного - серый в цвет окна. У скрытого слоя надписи серые, у видимого - белые.
    # Изменения внешнего вида производятся через изменение QPalette виджета
    def updatePalette(self) -> None:
        palette = self.palette()
        palette.setBrush(QPalette.Window, QBrush(QColor(
            0, 0, 255, alpha=64) if self.active else QColor(0, 0, 0, alpha=0), Qt.SolidPattern))
        palette.setBrush(QPalette.Text, QBrush(QColor(
            0, 0, 0) if self.visible else QColor(0, 0, 0, alpha=64), Qt.SolidPattern))
        self.setPalette(palette)

    # Обработчик нажатия self.activateButton, слот сигнала self.activateButton.clicked.
    # Если виджет уже активен, деакивирует его с сообщением сигнала deactivated, если нет,
    # активирует с сообщением сигнала activated. Затем согласно изменениям обновляется внешний вид виджета
    @pyqtSlot()
    def activate(self) -> None:
        if self.active:
            self.signals.deactivated.emit(self.index)
            self.active = False
        else:
            self.signals.activated.emit(self.index)
            self.active = True

        self.updatePalette()

    # Обработчик нажатия self.hideButton, слот сигнала self.hideButton.clicked.
    # Если виджет уже скрыт, делает его видимым с сообщением сигнала shown, если нет,
    # скрывает с сообщением сигнала hidden. Затем согласно изменениям обновляется внешний вид виджета
    @pyqtSlot()
    def changeVisibility(self) -> None:
        if self.visible:
            self.signals.hidden.emit(self.index)
            self.visible = False
        else:
            self.signals.shown.emit(self.index)
            self.visible = True

        self.updatePalette()

    # Слот сигнала self.moveUpButton.clicked. Сообщает сигнал movedUp. Вся работа по перемещению слоя
    # осуществляется в LayerList и Window
    @pyqtSlot()
    def moveUp(self) -> None:
        self.signals.movedUp.emit(self.index)

    # Слот сигнала self.moveDownButton.clicked. Сообщает сигнал movedDown. Вся работа по перемещению слоя
    # осуществляется в LayerList и Window
    @pyqtSlot()
    def moveDown(self) -> None:
        self.signals.movedDown.emit(self.index)

    # Слот сигнала self.deleteButton.clicked. Сообщает сигнал deleted. Вся работа по удалению слоя осуществляется
    # в LayerList и Window
    @pyqtSlot()
    def delete(self) -> None:
        self.signals.deleted.emit(self.index)
