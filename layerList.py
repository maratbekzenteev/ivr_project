from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtGui import QPalette, QBrush, QColor
from PyQt5.QtCore import Qt, pyqtSlot
from signals import LayerSignals
from layerListItem import LayerListItem


# Виджет списка слоёв для удобной манипуляции (скрытия, перемещения по высоте, ...) пользователем.
# Набор сигналов - LayerSignals. Поддерживает те же переменные для контроля к-ва и положения слоёв,
# что и Window, для удобства обращения к ним.
# Графические элементы:
# - self.layout - QVBoxLayout, выравнивает объекты LayerListItem по сетке, причем в порядке снизу вверх.
# - - Это сделано, чтобы новые слои добавлялись сверху, а не снизу: так пользователю легче понять, что слой выше всех
# - Объекты класса LayerListItem, в которых поддерживается вся необходимая информация о каждом слое в отдельности
# Аттрибуты:
# - self.hightestZ - int, класс, поддерживающий самое высокое значение self.z у любого из слоёв за все время
# - - (т.е. удаленные слои тоже считаются). Это нужно для нахождения "безопасного" значения self.z для нового слоя
# - self.layerCount - int, текущее к-во слоев
class LayerList(QWidget):
    # Инициализация графических элементов и аттрибутов
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setDirection(QVBoxLayout.BottomToTop)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)

        self.signals = LayerSignals()

        self.highestZ = 0
        self.layerCount = 0

        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setBrush(QPalette.Window, QBrush(QColor(255, 255, 255), Qt.SolidPattern))
        self.setPalette(palette)

    # Функция добавления нового растрового слоя. Добавляет слой выше остальных (на передний план),
    # обновляет переменные состояния, подключает сигналы к слотам
    def newBitmapLayer(self):
        self.layout.addWidget(LayerListItem(
            f'Холст ' + str(self.highestZ + 1), 'bmp', self.highestZ, self.layerCount))
        self.layerCount += 1
        self.highestZ += 1
        self.connectNewItem()

    def newImageLayer(self):
        self.layout.addWidget(LayerListItem(
            f'Картинка ' + str(self.highestZ + 1), 'img', self.highestZ, self.layerCount))
        self.layerCount += 1
        self.highestZ += 1
        self.connectNewItem()

    def connectNewItem(self):
        self.layout.itemAt(self.layerCount - 1).widget().signals.activated.connect(self.activateLayer)
        self.layout.itemAt(self.layerCount - 1).widget().signals.deactivated.connect(self.deactivateLayer)
        self.layout.itemAt(self.layerCount - 1).widget().signals.shown.connect(self.showLayer)
        self.layout.itemAt(self.layerCount - 1).widget().signals.hidden.connect(self.hideLayer)
        self.layout.itemAt(self.layerCount - 1).widget().signals.movedUp.connect(self.moveUpLayer)
        self.layout.itemAt(self.layerCount - 1).widget().signals.movedDown.connect(self.moveDownLayer)

    def newStaticLayer(self, name, z):
        self.layout.addWidget(LayerListItem(
            name, 'stl', z, self.layerCount, static=True))
        self.layerCount += 1
        self.highestZ += 1
        self.layout.itemAt(self.layerCount - 1).widget().signals.shown.connect(self.showLayer)
        self.layout.itemAt(self.layerCount - 1).widget().signals.hidden.connect(self.hideLayer)
        self.layout.itemAt(self.layerCount - 1).widget().updatePalette()

    # Активация слоя. Слот сигнала LayerListItem.activated. Итерируется по всем слоям и деактивирует, обновляя графику
    # (хранить индекс активированного слоя не на сцене, а в списке нецелесообразно в условиях адекватного к-ва слоев).
    # Сообщает сигнал activated. Необходимости итерироваться снова в поисках активированного виджета по индексу на сцене
    # не требуется, так как LayerListItem умеет это делать сам уже после сообщения сигнала
    @pyqtSlot(int)
    def activateLayer(self, index: int) -> None:
        for i in range(self.layerCount):
            self.layout.itemAt(i).widget().active = False
            self.layout.itemAt(i).widget().updatePalette()

        self.signals.activated.emit(index)

    # Дективация слоя. Слот сигнала LayerListItem.deactivated. Итерируется по всем слоям и деактивирует, обновляя
    # (хранить индекс активированного слоя не на сцене, а в списке нецелесообразно в условиях адекватного к-ва слоев).
    # Сообщает сигнал deactivated
    @pyqtSlot(int)
    def deactivateLayer(self, index: int) -> None:
        for i in range(self.layerCount):
            self.layout.itemAt(i).widget().active = False
            self.layout.itemAt(i).widget().updatePalette()

        self.signals.deactivated.emit(index)

    # Слот сигнала LayerListItem.shown. Сообщает сигнал shown, сам не делает ничего, так как внешний вид виджет
    # обновляет сам, а показ на сцене осуществляет класс Window
    @pyqtSlot(int)
    def showLayer(self, index: int) -> None:
        self.signals.shown.emit(index)

    # Слот сигнала LayerListItem.hidden. Сообщает сигнал hidden, сам не делает ничего, так как внешний вид виджет
    # обновляет сам, а скрытие на сцене осуществляет класс Window
    @pyqtSlot(int)
    def hideLayer(self, index: int) -> None:
        self.signals.hidden.emit(index)

    # Функция перемещения слоя выше в списке. Слот сигнала LayerListItem.movedUp
    @pyqtSlot(int)
    def moveUpLayer(self, index: int) -> None:
        # Слой с таким индексом на сцене ищется среди всех за линейное время
        inListIndex = -1
        for i in range(self.layerCount):
            if self.layout.itemAt(i).widget().index == index:
                inListIndex = i
                break

        # Если слой и так выше всех, то есть имеет наибольший возможный индекс в списке, нельзя переместить => выходим
        if inListIndex == self.layerCount - 1:
            return

        # Далее меняются местами свойства найденного LayerListItem и того, что выше него на 1 (имеет больший на 1 индекс
        # в списке). Местами меняются именно свойства, а не сами объекты, так как Qt не предоставляет возможности
        # сделать это, не затрагивая другие виджеты

        # Через вспомогательные переменные меняются местами имена слоев
        aName = self.layout.itemAt(inListIndex).widget().nameField.text()
        bName = self.layout.itemAt(inListIndex + 1).widget().nameField.text()
        self.layout.itemAt(inListIndex).widget().nameField.setText(bName)
        self.layout.itemAt(inListIndex + 1).widget().nameField.setText(aName)

        # Распаковкой кортежа меняются местами высоты слоев
        self.layout.itemAt(inListIndex).widget().z, self.layout.itemAt(inListIndex + 1).widget().z = \
            self.layout.itemAt(inListIndex + 1).widget().z, self.layout.itemAt(inListIndex).widget().z

        # Распаковкой кортежа меняются местами индексы слоев на сцене
        self.layout.itemAt(inListIndex).widget().index, self.layout.itemAt(inListIndex + 1).widget().index = \
            self.layout.itemAt(inListIndex + 1).widget().index, self.layout.itemAt(inListIndex).widget().index

        # Распаковкой кортежа меняются местами типы слоев
        self.layout.itemAt(inListIndex).widget().type, self.layout.itemAt(inListIndex + 1).widget().type = \
            self.layout.itemAt(inListIndex + 1).widget().type, self.layout.itemAt(inListIndex).widget().type

        # Распаковкой кортежа меняются местами аттрибуты видимости слоев
        self.layout.itemAt(inListIndex).widget().visible, self.layout.itemAt(inListIndex + 1).widget().visible = \
            self.layout.itemAt(inListIndex + 1).widget().visible, self.layout.itemAt(inListIndex).widget().visible

        # Распаковкой кортежа меняются местами аттрибуты активности слоев
        self.layout.itemAt(inListIndex).widget().active, self.layout.itemAt(inListIndex + 1).widget().active = \
            self.layout.itemAt(inListIndex + 1).widget().active, self.layout.itemAt(inListIndex).widget().active

        # Внешний вид LayerListItem обновляется согласно новым данным
        self.layout.itemAt(inListIndex).widget().updatePalette()
        self.layout.itemAt(inListIndex + 1).widget().updatePalette()

        # Сигналом swappedLayers сообщается необходимость поменять 2 слоя местами на сцене
        self.signals.swappedLayers.emit(index, self.layout.itemAt(inListIndex).widget().index)

    # Функция перемещения слоя ниже в списке. Слот сигнала LayerListItem.movedDown
    @pyqtSlot(int)
    def moveDownLayer(self, index: int) -> None:
        # Слой с таким индексом на сцене ищется среди всех за линейное время
        inListIndex = -1
        for i in range(self.layerCount):
            if self.layout.itemAt(i).widget().index == index:
                inListIndex = i
                break

        # Если слой и так ниже всех, то есть имеет наименьший возможный индекс в списке, нельзя переместить => выходим
        if inListIndex == 2:
            return

        # Далее меняются местами свойства найденного LayerListItem и того, что ниже него на 1 (имеет меньший на 1 индекс
        # в списке). Местами меняются именно свойства, а не сами объекты, так как Qt не предоставляет возможности
        # сделать это, не затрагивая другие виджеты

        # Через вспомогательные переменные меняются местами имена слоев
        aName = self.layout.itemAt(inListIndex).widget().nameField.text()
        bName = self.layout.itemAt(inListIndex - 1).widget().nameField.text()
        self.layout.itemAt(inListIndex).widget().nameField.setText(bName)
        self.layout.itemAt(inListIndex - 1).widget().nameField.setText(aName)

        # Распаковкой кортежа меняются местами высоты слоев
        self.layout.itemAt(inListIndex).widget().z, self.layout.itemAt(inListIndex - 1).widget().z = \
            self.layout.itemAt(inListIndex - 1).widget().z, self.layout.itemAt(inListIndex).widget().z

        # Распаковкой кортежа меняются местами индексы слоев на сцене
        self.layout.itemAt(inListIndex).widget().index, self.layout.itemAt(inListIndex - 1).widget().index = \
            self.layout.itemAt(inListIndex - 1).widget().index, self.layout.itemAt(inListIndex).widget().index

        # Распаковкой кортежа меняются местами типы слоев
        self.layout.itemAt(inListIndex).widget().type, self.layout.itemAt(inListIndex - 1).widget().type = \
            self.layout.itemAt(inListIndex - 1).widget().type, self.layout.itemAt(inListIndex).widget().type

        # Распаковкой кортежа меняются местами аттрибуты видимости слоев
        self.layout.itemAt(inListIndex).widget().visible, self.layout.itemAt(inListIndex - 1).widget().visible = \
            self.layout.itemAt(inListIndex - 1).widget().visible, self.layout.itemAt(inListIndex).widget().visible

        # Распаковкой кортежа меняются местами аттрибуты активности слоев
        self.layout.itemAt(inListIndex).widget().active, self.layout.itemAt(inListIndex - 1).widget().active = \
            self.layout.itemAt(inListIndex - 1).widget().active, self.layout.itemAt(inListIndex).widget().active

        # Внешний вид LayerListItem обновляется согласно новым данным
        self.layout.itemAt(inListIndex).widget().updatePalette()
        self.layout.itemAt(inListIndex - 1).widget().updatePalette()

        # Сигналом swappedLayers сообщается необходимость поменять 2 слоя местами на сцене
        self.signals.swappedLayers.emit(index, self.layout.itemAt(inListIndex).widget().index)
