from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QPushButton, QGridLayout
from PyQt5.QtGui import QPalette, QBrush, QColor
from PyQt5.QtCore import Qt, pyqtSlot
from client.src.signals import LayerSignals
from client.gui.layerListItem import LayerListItem


# Виджет списка слоёв для удобной манипуляции (скрытия, перемещения по высоте, ...) пользователем.
# Набор сигналов - LayerSignals. Поддерживает те же переменные для контроля к-ва и положения слоёв,
# что и Window, для удобства обращения к ним.
# Графические элементы:
# - self.outerLayout - QGridLayout, выравнивает объекты LayerListItem по сетке. В него входят:
# - - self.newBitmapButton
# - - self.newImageButton
# - - self.newShapeButton
# - - self.newTextButton
# - - self.scrollArea
# - self.scrollArea - QScrollArea, прокручиваемая область, в которой отображаются все LayerListItem. Виджет,
# - - отвечающий за содержимое области - self.itemContainer
# - self.itemContainer - QWidget, отображается внутри self.scrollArea
# - self.layout - QVBoxLayout, сетка, выравнивающая и упорядочивающая LayerListItem внутри self.itemContainer,
# - - причем в порядке снизу вверх. Это сделано, чтобы новые слои добавлялись сверху, а не снизу:
# - - так пользователю легче понять, что слой выше всех
# - Объекты класса LayerListItem, в которых поддерживается вся необходимая информация о каждом слое в отдельности
# - self.newBitmapButton - QPushButton, кнопка добавления холста. Вызывает слот parent.addBitmapLayer
# - self.newImageButton - QPushButton, кнопка добавления слоя-картинки. Вызывает слот parent.addImageLayer
# - self.newShapeButton - QPushButton, кнопка добавления фигурного слоя. Вызывает слот parent.addShapeLayer
# - self.newTextButton - QPushButton, кнопка добавления текстового слоя. Вызывает слот addTextLayer,
# где parent - слой родительского виджета класса Window (см. main.py), в котором находится список слоёв
# Атрибуты:
# - self.highestZ - int (после загрузки из файла - целочисленный float),
# - - класс, поддерживающий самое высокое значение self.z у любого из слоёв за все время
# - - (т.е. удаленные слои тоже считаются). Это нужно для нахождения "безопасного" значения self.z для нового слоя
# - self.layerCount - int, текущее к-во слоев
class LayerList(QWidget):
    # Инициализация графических элементов и атрибутов
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)

        self.parent = parent

        self.setMinimumWidth(270)
        self.outerLayout = QGridLayout(self)
        self.outerLayout.setSpacing(0)
        self.outerLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.outerLayout)

        self.newBitmapButton = QPushButton('')
        self.newBitmapButton.setToolTip('Новый холст')
        self.newImageButton = QPushButton('')
        self.newImageButton.setToolTip('Новый слой-картинка')
        self.newShapeButton = QPushButton('')
        self.newShapeButton.setToolTip('Новый фигурный слой')
        self.newTextButton = QPushButton('')
        self.newTextButton.setToolTip('Новый текстовый слой')

        self.newBitmapButton.clicked.connect(self.parent.addBitmapLayer)
        self.newImageButton.clicked.connect(self.parent.addImageLayer)
        self.newShapeButton.clicked.connect(self.parent.addShapeLayer)
        self.newTextButton.clicked.connect(self.parent.addTextLayer)
        self.outerLayout.addWidget(self.newBitmapButton, 0, 0)
        self.outerLayout.addWidget(self.newImageButton, 0, 1)
        self.outerLayout.addWidget(self.newShapeButton, 0, 2)
        self.outerLayout.addWidget(self.newTextButton, 0, 3)

        self.scrollArea = QScrollArea()
        self.scrollArea.setMinimumWidth(270)
        self.outerLayout.addWidget(self.scrollArea, 1, 0, 1, 4, Qt.AlignJustify)
        self.itemContainer = QWidget()
        self.scrollArea.setWidget(self.itemContainer)
        self.scrollArea.setWidgetResizable(True)

        self.layout = QVBoxLayout(self)
        self.layout.setDirection(QVBoxLayout.BottomToTop)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.layout.setSpacing(0)
        self.itemContainer.setLayout(self.layout)

        self.signals = LayerSignals()

        self.highestZ = 0
        self.layerCount = 0

        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setBrush(QPalette.Window, QBrush(QColor(255, 255, 255), Qt.SolidPattern))
        self.setPalette(palette)

    # Функция добавления нового растрового слоя ("холста"). При загрузке из файла (заполнены опциональные параметры)
    # восстанавливает все атрибуты из него, иначе добавляет слой выше остальных (на передний план).
    # Обновляет переменные состояния, подключает сигналы к слотам. Вызывается родительским классом
    def newBitmapLayer(self, z=-1, index=-1, name='') -> None:
        if index == -1:
            self.layout.addWidget(LayerListItem(
                f'Холст ' + str(self.highestZ - 1), 'bmp', self.highestZ, self.layerCount))
        else:
            self.layout.addWidget(LayerListItem(name if name != '' else f'Холст ' + str(self.highestZ - 1),
                                                'bmp', z, index))
        self.layerCount += 1
        self.highestZ += 1
        self.connectNewItem()

    # Функция добавления нового слоя-картинки. При загрузке из файла (заполнены опциональные параметры)
    # восстанавливает все атрибуты из него, иначе добавляет слой выше остальных (на передний план).
    # Обновляет переменные состояния, подключает сигналы к слотам. Вызывается родительским классом
    def newImageLayer(self, z=-1, index=-1, name='') -> None:
        if index == -1:
            self.layout.addWidget(LayerListItem(
                f'Картинка ' + str(self.highestZ - 1), 'img', self.highestZ, self.layerCount))
        else:
            self.layout.addWidget(LayerListItem(name if name != '' else f'Картинка ' + str(self.highestZ - 1),
                                                'img', z, index))
        self.layerCount += 1
        self.highestZ += 1
        self.connectNewItem()

    # Функция добавления нового фигурного слоя. При загрузке из файла (заполнены опциональные параметры)
    # восстанавливает все атрибуты из него, иначе добавляет слой выше остальных (на передний план).
    # Обновляет переменные состояния, подключает сигналы к слотам. Вызывается родительским классом
    def newShapeLayer(self, z=-1, index=-1, name='') -> None:
        if index == -1:
            self.layout.addWidget(LayerListItem(
                f'Фигура ' + str(self.highestZ - 1), 'shp', self.highestZ, self.layerCount))
        else:
            self.layout.addWidget(LayerListItem(name if name != '' else f'Фигура ' + str(self.highestZ - 1),
                                                'shp', z, index))
        self.layerCount += 1
        self.highestZ += 1
        self.connectNewItem()

    # Функция добавления нового текстового слоя. При загрузке из файла (заполнены опциональные параметры)
    # восстанавливает все атрибуты из него, иначе добавляет слой выше остальных (на передний план).
    # Обновляет переменные состояния, подключает сигналы к слотам. Вызывается родительским классом
    def newTextLayer(self, z=-1, index=-1, name='') -> None:
        if index == -1:
            self.layout.addWidget(LayerListItem(
                f'Надпись ' + str(self.highestZ - 1), 'txt', self.highestZ, self.layerCount))
        else:
            self.layout.addWidget(LayerListItem(name if name != '' else f'Надпись ' + str(self.highestZ - 1),
                                                'txt', z, index))
        self.layerCount += 1
        self.highestZ += 1
        self.connectNewItem()

    # Функция подключения графических элементов нового LayerListItem к соответствующим слотам. Вызывается при добавлении
    # любого динамического слоя (холста, картинки, фигуры, текстового). Вызывается самим классом LayerList
    def connectNewItem(self) -> None:
        self.layout.itemAt(self.layerCount - 1).widget().signals.activated.connect(self.activateLayer)
        self.layout.itemAt(self.layerCount - 1).widget().signals.deactivated.connect(self.deactivateLayer)
        self.layout.itemAt(self.layerCount - 1).widget().signals.shown.connect(self.showLayer)
        self.layout.itemAt(self.layerCount - 1).widget().signals.hidden.connect(self.hideLayer)
        self.layout.itemAt(self.layerCount - 1).widget().signals.movedUp.connect(self.moveUpLayer)
        self.layout.itemAt(self.layerCount - 1).widget().signals.movedDown.connect(self.moveDownLayer)
        self.layout.itemAt(self.layerCount - 1).widget().signals.deleted.connect(self.deleteLayer)
        self.activateLayer(self.layerCount - 1)
        self.layout.itemAt(self.layerCount - 1).widget().active = True
        self.layout.itemAt(self.layerCount - 1).widget().updatePalette()

    # Функция создания и подключения нового статического слоя (фона, сетки). Таким слоям присвоены определенные
    # параметры, неизменные на протяжении всей работы с файлом (у фона z=0, у сетки z=1024), они передаются в функцию
    # создания как аргументы. Вызывается родительским классом
    def newStaticLayer(self, name: str, z: int) -> None:
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

    # Функция деактивации всех слоёв. Вызывается родительским классом(в частности говоря, при сохранении и экспорте
    # проекта). Это нужно, чтобы все текстовые слои отображались на своём месте, а не поверх других (чтобы в файле
    # сохранилось корректное их значение z), а также чтобы на слоях не рисовались вспомогательные элементы
    def deactivateAll(self) -> None:
        for i in range(self.layerCount):
            self.layout.itemAt(i).widget().active = False
            self.layout.itemAt(i).widget().updatePalette()

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

        # Распаковкой кортежа меняются местами атрибуты видимости слоев
        self.layout.itemAt(inListIndex).widget().visible, self.layout.itemAt(inListIndex + 1).widget().visible = \
            self.layout.itemAt(inListIndex + 1).widget().visible, self.layout.itemAt(inListIndex).widget().visible

        # Распаковкой кортежа меняются местами атрибуты активности слоев
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

        # Распаковкой кортежа меняются местами атрибуты видимости слоев
        self.layout.itemAt(inListIndex).widget().visible, self.layout.itemAt(inListIndex - 1).widget().visible = \
            self.layout.itemAt(inListIndex - 1).widget().visible, self.layout.itemAt(inListIndex).widget().visible

        # Распаковкой кортежа меняются местами атрибуты активности слоев
        self.layout.itemAt(inListIndex).widget().active, self.layout.itemAt(inListIndex - 1).widget().active = \
            self.layout.itemAt(inListIndex - 1).widget().active, self.layout.itemAt(inListIndex).widget().active

        # Внешний вид LayerListItem обновляется согласно новым данным
        self.layout.itemAt(inListIndex).widget().updatePalette()
        self.layout.itemAt(inListIndex - 1).widget().updatePalette()

        # Сигналом swappedLayers сообщается необходимость поменять 2 слоя местами на сцене
        self.signals.swappedLayers.emit(index, self.layout.itemAt(inListIndex).widget().index)

    # Фунция удаления слоя. Обновляет номер текущего слоя, если удаляется он, ищет индекс в сетке, обновляет атрибуты
    # класса. Слот сигнала LayerListItem.deleted, также вызывается для всех слоёв самим классом при работе self.clear.
    # Сообщает сигнал self.deleted
    @pyqtSlot(int)
    def deleteLayer(self, index: int) -> None:
        if self.parent.currentLayer == index:
            self.signals.deactivated.emit(index)
        elif self.parent.currentLayer > index:
            self.parent.currentLayer -= 1

        inListIndex = -1
        for i in range(self.layerCount):
            if self.layout.itemAt(i).widget().index == index:
                inListIndex = i
            elif self.layout.itemAt(i).widget().index > index:
                self.layout.itemAt(i).widget().index -= 1

        self.layerCount -= 1
        deletedWidget = self.layout.itemAt(inListIndex).widget()
        self.layout.removeWidget(deletedWidget)

        self.signals.deleted.emit(index)

    # Фунция очистки (удаления всех слоёв). Вызывается родительским классом при открытии проекта или создании нового
    def clear(self) -> None:
        self.deactivateLayer(0)
        for i in range(self.layerCount - 1, -1, -1):
            self.deleteLayer(i)
        self.highestZ = 0

    # Функция получения названия слоя. Вызывается родительским классом при сохранении проекта
    def getName(self, index: int) -> str:
        for i in range(self.layerCount):
            if self.layout.itemAt(i).widget().index == index:
                return self.layout.itemAt(i).widget().nameField.text()

        return ''
