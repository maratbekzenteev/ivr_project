import sys
from PyQt5.QtWidgets import (QApplication, QGraphicsScene, QGraphicsView, QTabWidget, QLabel,
                             QWidget, QListWidget, QPushButton, QGridLayout, QShortcut)
from PyQt5.QtGui import QPixmap, QFont, QKeySequence, QColor
from PyQt5.QtCore import Qt, QRect
from bitmap_layer import BitmapLayer
from grid_layer import GridLayer
from background_layer import BackgroundLayer
from gui_classes import BitmapToolbar, LayerToolbar, GridToolbar, LayerList

# Договорённости по именованию переменных:
# - Названия переменных пишутся в стиле camelCase, чтобы избежать смешения двух стилей (в PyQt всё пишется этим стилем)
# - Названия классов отображают, что это за класс (кнопка, превью, список, ...)
# - Названия сигналов пишутся в форме Past Participle (clicked, shown, valueChanged, ...)
# - Названия функций-слотов пишутся в форме инфинитива (addWidget, updateLayerState, swapLayers, ...)


# Класс Window - класс главного окна программы.
# Выровнен по QGridLayout, содержит в себе (вложенно) все виджеты программы.
# Переменные:
# - self.layout - QGridLayout, сетка выравнивания виджетов в окне.
# - self.tab - QTabWidget, содержащий виджеты панелей инструментов со всем основным функционалом (см. gui_classes.py)
# - self.preview - QGraphicsView, "рабочая область" окна. Отображает сцену self.scene
# - self.layers - LayerList (см. gui_classes.py), меню управления слоями (скрытие, выделение, передний/задний план,...)
# - self.scene - QGraphicsScene, сцена со всеми слоями, включая слой с задним фоном
# - self.currentLayer - int, индекс слоя, с которым пользователь может взаимодействовать. Нумеруются с нуля (-1 - ни
# - - один слой не выделен). Для перевода в индексацию self.scene прибавить 1
# - self.highestZ - int, текущая "высота" самого высокого слоя. Поддерживается также в LayerList
# - self.resolution - tuple(int, int), разрешение целевого изображения проекта
class Window(QWidget):
    # Инициализация графических элементов, подключение сигналов к слотам
    def __init__(self):
        super().__init__()
        self.setFont(QFont("Segoe UI", 12))

        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self.currentLayer = -1
        self.highestZ = 0
        self.resolution = 1280, 720

        self.layers = LayerList(self)
        self.preview = QGraphicsView(self)
        self.tab = QTabWidget(self)

        self.tab.addTab(BitmapToolbar(), "Рисование")
        self.tab.widget(0).signals.valueChanged.connect(self.updateLayerState)

        self.tab.addTab(LayerToolbar(), "Слои")
        self.tab.widget(1).newBitmapLayerButton.clicked.connect(self.addBitmapLayer)

        self.tab.addTab(GridToolbar(self.resolution), "Сетка")
        self.tab.widget(2).signals.added.connect(self.addGridLine)
        self.tab.widget(2).signals.deleted.connect(self.deleteGridLine)

        self.layers.signals.activated.connect(self.activateLayer)
        self.layers.signals.deactivated.connect(self.deactivateLayer)
        self.layers.signals.shown.connect(self.showLayer)
        self.layers.signals.hidden.connect(self.hideLayer)
        self.layers.signals.swappedLayers.connect(self.swapLayers)

        self.layout.addWidget(self.layers, 1, 0)
        self.layout.addWidget(self.preview, 1, 1, alignment=Qt.AlignCenter)
        self.layout.addWidget(self.tab, 0, 0, 1, 2, Qt.AlignTop)
        self.layout.setColumnStretch(1, 1)

        self.zoomInShortcut = QShortcut(QKeySequence("Ctrl+="), self)
        self.zoomInShortcut.activated.connect(self.zoomIn)

        self.zoomOutShortcut = QShortcut(QKeySequence("Ctrl+-"), self)
        self.zoomOutShortcut.activated.connect(self.zoomOut)

        self.scene = QGraphicsScene(self)
        self.scene.setItemIndexMethod(-1)
        self.scene.addWidget(BackgroundLayer(*self.resolution))
        self.scene.addWidget(GridLayer(*self.resolution))
        self.scene.items()[-1].setZValue(1024)
        self.preview.setScene(self.scene)

        self.layers.newStaticLayer('Фон', 0)
        self.layers.newStaticLayer('Сетка', 1024)

        self.show()

    # Слот для self.zoomInShortcut, увеличивает масштаб отображения в рабочей области в 5/4 раза
    def zoomIn(self):
        self.preview.scale(1.25, 1.25)

    # Слот для self.zoomOutShortcut, увеличивает масштаб отображения в рабочей области в 4/5 раза
    def zoomOut(self):
        self.preview.scale(0.8, 0.8)

    # Добавление нового растрового слоя.
    # Слот для self.tab.widget(1).newBitmapLayerButton.clicked, увеличивает макс. высоту слоя,
    # добавляет слой на сцену (как и любой слой, в виде QProxyWidget) и в список слоёв.
    def addBitmapLayer(self):
        self.highestZ += 1
        self.scene.addWidget(BitmapLayer(*self.resolution, self))
        self.scene.items()[-1].setZValue(self.highestZ)
        self.layers.newBitmapLayer()

    # Обновление цвета, толщины и инструмента рисования на слое. В будущем содержимое будет передаваться в классе State
    # Вызывается как слот при изменении состояния панели BitmapToolbar (сигнал valueChanged)
    def updateLayerState(self):
        if self.currentLayer != -1:
            self.scene.items()[self.currentLayer].widget().updateState(self.tab.widget(0).color,
                                                                           self.tab.widget(0).width,
                                                                           self.tab.widget(0).tool)

    # Активация выделенного через меню слоя. Слот для self.layers.signals.activated.
    # Снимает выделение с ранее выделенного слоя (если таковой был), делает активным текущий выделенный слой,
    # передаёт состояние панели инструментов на случай, если её состояние поменяли, пока активным был другой слой,
    # обновляет переменную self.currentLayer
    def activateLayer(self, index: int) -> None:
        if self.currentLayer != -1:
            self.scene.items()[self.currentLayer].widget().active = False
        self.scene.items()[index].widget().active = True
        self.currentLayer = index

        self.updateLayerState()

    # Деактивация слоя. Слот для self.layers.signals.deactivated.
    # Снимает выделение с ранее выделенного слоя (который и послал сигнал),
    # сообщает в self.currentLayer, что никакой слой не выделен.
    def deactivateLayer(self, index: int) -> None:
        self.scene.items()[index].widget().active = False
        self.currentLayer = -1

    # Показывает слой. Слот для self.layers.signals.shown
    def showLayer(self, index: int) -> None:
        self.scene.items()[index].widget().show()

    # Скрывает слой. Слот для self.layers.signals.hidden
    def hideLayer(self, index: int) -> None:
        self.scene.items()[index].widget().hide()

    # Обменивает слои их высотами (один перемещается под другой). Слот для self.layers.signals.swappedLayers.
    # Используется при перемещении слоя пользователем как выше, так и ниже.
    def swapLayers(self, indexA: int, indexB: int) -> None:
        aValue = self.scene.items()[indexA].zValue()
        bValue = self.scene.items()[indexB].zValue()
        self.scene.items()[indexA].setZValue(bValue)
        self.scene.items()[indexB].setZValue(aValue)

    def addGridLine(self, direction: int, indentType: int, indent: int) -> None:
        self.scene.items()[1].widget().addLine(direction, indentType, indent)

    def deleteGridLine(self, direction: int, indentType: int, indent: int) -> None:
        self.scene.items()[1].widget().deleteLine(direction, indentType, indent)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())
