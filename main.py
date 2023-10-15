import sys
from PyQt5.QtWidgets import (QApplication, QGraphicsScene, QGraphicsView, QTabWidget, QLabel,
                             QWidget, QListWidget, QPushButton, QGridLayout, QShortcut, QScrollArea)
from PyQt5.QtGui import QPixmap, QFont, QKeySequence, QColor
from PyQt5.QtCore import Qt, QRect, pyqtSlot
from bitmapLayer import BitmapLayer
from gridLayer import GridLayer
from imageLayer import ImageLayer
from shapeLayer import ShapeLayer
from textLayer import TextLayer
from backgroundLayer import BackgroundLayer
from bitmapToolbar import BitmapToolbar
from imageToolbar import ImageToolbar
from layerToolbar import LayerToolbar
from gridToolbar import GridToolbar
from shapeToolbar import ShapeToolbar
from textToolbar import TextToolbar
from layerList import LayerList


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
        # self.setFont(QFont("Segoe UI", 12))
        self.setFont(QFont("Verdana", 12))

        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self.currentLayer = -1
        self.highestZ = 0
        self.resolution = 1280, 720

        self.layers = LayerList(self)
        self.preview = QGraphicsView(self)
        self.tab = QTabWidget(self)
        self.tab.setMaximumHeight(196)

        self.tab.addTab(BitmapToolbar(), "Холст")
        self.tab.widget(0).signals.valueChanged.connect(self.updateBitmapLayerState)

        self.tab.addTab(LayerToolbar(), "Слои")
        self.tab.widget(1).newBitmapLayerButton.clicked.connect(self.addBitmapLayer)
        self.tab.widget(1).newImageLayerButton.clicked.connect(self.addImageLayer)
        self.tab.widget(1).newShapeLayerButton.clicked.connect(self.addShapeLayer)

        self.tab.addTab(GridToolbar(self.resolution), "Сетка")
        self.tab.widget(2).signals.added.connect(self.addGridLine)
        self.tab.widget(2).signals.deleted.connect(self.deleteGridLine)

        self.tab.addTab(ImageToolbar(), "Картинка")
        self.tab.widget(3).signals.stateChanged.connect(self.updateImageLayerState)
        self.tab.widget(3).signals.imageChanged.connect(self.updateImageLayerImage)

        self.tab.addTab(ShapeToolbar(), "Фигура")
        self.tab.widget(4).signals.valueChanged.connect(self.updateShapeLayerState)

        self.tab.addTab(TextToolbar(), "Текст")
        self.tab.widget(5).signals.valueChanged.connect(self.updateTextLayerState)

        self.layers.signals.activated.connect(self.activateLayer)
        self.layers.signals.deactivated.connect(self.deactivateLayer)
        self.layers.signals.shown.connect(self.showLayer)
        self.layers.signals.hidden.connect(self.hideLayer)
        self.layers.signals.swappedLayers.connect(self.swapLayers)
        self.layers.signals.deleted.connect(self.deleteLayer)

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

        # self.scene.addWidget(ImageLayer('tmp_icon.png', *self.resolution))

        self.layers.newStaticLayer('Фон', 0)
        self.layers.newStaticLayer('Сетка', 1024)

        self.show()

    # Слот для self.zoomInShortcut, увеличивает масштаб отображения в рабочей области в 5/4 раза
    @pyqtSlot()
    def zoomIn(self):
        self.preview.scale(1.25, 1.25)

    # Слот для self.zoomOutShortcut, увеличивает масштаб отображения в рабочей области в 4/5 раза
    @pyqtSlot()
    def zoomOut(self):
        self.preview.scale(0.8, 0.8)

    # Добавление нового растрового слоя.
    # Слот для self.tab.widget(1).newBitmapLayerButton.clicked, увеличивает макс. высоту слоя,
    # добавляет слой на сцену (как и любой слой, в виде QProxyWidget) и в список слоёв.
    @pyqtSlot()
    def addBitmapLayer(self):
        self.highestZ += 1
        self.scene.addWidget(BitmapLayer(*self.resolution, self))
        self.scene.items()[-1].setZValue(self.highestZ)
        self.layers.newBitmapLayer()

    @pyqtSlot()
    def addImageLayer(self):
        self.highestZ += 1
        self.scene.addWidget(ImageLayer('tmp_icon.png', *self.resolution, self))
        self.scene.items()[-1].setZValue(self.highestZ)
        self.layers.newImageLayer()

    @pyqtSlot()
    def addShapeLayer(self):
        self.highestZ += 1
        self.scene.addWidget(ShapeLayer(*self.resolution, self))
        self.scene.items()[-1].setZValue(self.highestZ)
        self.layers.newShapeLayer()

    @pyqtSlot()
    def addTextLayer(self):
        self.highestZ += 1
        self.scene.addWidget(TextLayer(*self.resolution, self))
        self.scene.items()[-1].setZValue(self.highestZ)
        self.layers.newTextLayer()

    # Обновление цвета, толщины и инструмента рисования на слое
    # Вызывается как слот при изменении состояния панели BitmapToolbar (сигнал valueChanged)
    @pyqtSlot()
    def updateBitmapLayerState(self):
        if self.currentLayer != -1 and isinstance(self.scene.items()[self.currentLayer].widget(), BitmapLayer):
            self.scene.items()[self.currentLayer].widget().updateState(self.tab.widget(0).color,
                                                                           self.tab.widget(0).width,
                                                                           self.tab.widget(0).tool)

    @pyqtSlot(int, str, str)
    def updateImageLayerState(self, size, alignment, tool):
        if self.currentLayer != -1 and isinstance(self.scene.items()[self.currentLayer].widget(), ImageLayer):
            self.scene.items()[self.currentLayer].widget().updateState(size, alignment, tool)

    @pyqtSlot(str)
    def updateImageLayerImage(self, imagePath):
        if self.currentLayer != -1 and isinstance(self.scene.items()[self.currentLayer].widget(), ImageLayer):
            self.scene.items()[self.currentLayer].widget().updateImage(imagePath)

    def updateImageToolbarState(self):
        self.tab.widget(3).filePath = self.scene.items()[self.currentLayer].widget().imagePath
        self.tab.widget(3).size = self.scene.items()[self.currentLayer].widget().size
        self.tab.widget(3).alignmentSelector.setState(self.scene.items()[self.currentLayer].widget().alignment)
        self.tab.widget(3).toolSelector.setState(self.scene.items()[self.currentLayer].widget().tool)

    @pyqtSlot()
    def updateShapeLayerState(self):
        if self.currentLayer != -1 and isinstance(self.scene.items()[self.currentLayer].widget(), ShapeLayer):
            self.scene.items()[self.currentLayer].widget().updateState(self.tab.widget(4).lineColor,
                                                                       self.tab.widget(4).fillColor,
                                                                       self.tab.widget(4).width,
                                                                       self.tab.widget(4).tool,
                                                                       self.tab.widget(4).shape)

    def updateShapeToolbarState(self):
        self.tab.widget(4).setState(self.scene.items()[self.currentLayer].widget().lineColor,
                                    self.scene.items()[self.currentLayer].widget().fillColor,
                                    self.scene.items()[self.currentLayer].widget().width,
                                    self.scene.items()[self.currentLayer].widget().tool,
                                    self.scene.items()[self.currentLayer].widget().shape)

    @pyqtSlot()
    def updateTextLayerState(self):
        if self.currentLayer != -1 and isinstance(self.scene.items()[self.currentLayer].widget(), TextLayer):
            self.scene.items()[self.currentLayer].widget().updateState(self.tab.widget(5).color,
                                                                       self.tab.widget(5).font,
                                                                       self.tab.widget(5).size,
                                                                       self.tab.widget(5).fontWeight,
                                                                       self.tab.widget(5).italic,
                                                                       self.tab.widget(5).underline,
                                                                       self.tab.widget(5).alignment)

    def updateTextToolbarState(self):
        self.tab.widget(5).setState(self.scene.items()[self.currentLayer].widget().color,
                                    self.scene.items()[self.currentLayer].widget().font,
                                    self.scene.items()[self.currentLayer].widget().size,
                                    self.scene.items()[self.currentLayer].widget().fontWeight,
                                    self.scene.items()[self.currentLayer].widget().italic,
                                    self.scene.items()[self.currentLayer].widget().underline,
                                    self.scene.items()[self.currentLayer].widget().alignment)

    # Активация выделенного через меню слоя. Слот для self.layers.signals.activated.
    # Снимает выделение с ранее выделенного слоя (если таковой был), делает активным текущий выделенный слой,
    # передаёт состояние панели инструментов на случай, если её состояние поменяли, пока активным был другой слой,
    # обновляет переменную self.currentLayer
    @pyqtSlot(int)
    def activateLayer(self, index: int) -> None:
        if self.currentLayer != -1:
            self.scene.items()[self.currentLayer].widget().active = False
            if isinstance(self.scene.items()[self.currentLayer].widget(), TextLayer):
                self.scene.items()[self.currentLayer].setZValue(self.scene.items()[self.currentLayer].widget()
                                                                .previousZValue)

        self.scene.items()[index].widget().active = True
        self.currentLayer = index

        for i in range(len(self.scene.items())):
            self.scene.items()[i].widget().setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.scene.items()[self.currentLayer].widget().setAttribute(Qt.WA_TransparentForMouseEvents, False)

        if isinstance(self.scene.items()[self.currentLayer].widget(), BitmapLayer):
            self.updateBitmapLayerState()
        elif isinstance(self.scene.items()[self.currentLayer].widget(), ImageLayer):
            self.updateImageToolbarState()
        elif isinstance(self.scene.items()[self.currentLayer].widget(), ShapeLayer):
            self.updateShapeToolbarState()
        elif isinstance(self.scene.items()[self.currentLayer].widget(), TextLayer):
            self.scene.items()[self.currentLayer].widget().storeZValue(self.scene.items()[self.currentLayer].zValue())
            self.scene.items()[self.currentLayer].setZValue(1023)
            self.updateTextToolbarState()

    # Деактивация слоя. Слот для self.layers.signals.deactivated.
    # Снимает выделение с ранее выделенного слоя (который и послал сигнал),
    # сообщает в self.currentLayer, что никакой слой не выделен.
    @pyqtSlot(int)
    def deactivateLayer(self, index: int) -> None:
        if isinstance(self.scene.items()[self.currentLayer].widget(), TextLayer):
            self.scene.items()[self.currentLayer].setZValue(self.scene.items()[self.currentLayer].widget()
                                                            .previousZValue)

        self.scene.items()[index].widget().active = False
        self.currentLayer = -1

    # Показывает слой. Слот для self.layers.signals.shown
    @pyqtSlot(int)
    def showLayer(self, index: int) -> None:
        self.scene.items()[index].widget().show()

    # Скрывает слой. Слот для self.layers.signals.hidden
    @pyqtSlot(int)
    def hideLayer(self, index: int) -> None:
        self.scene.items()[index].widget().hide()

    @pyqtSlot(int)
    def deleteLayer(self, index):
        deletedItem = self.scene.items()[index]
        self.scene.removeItem(deletedItem)

    # Обменивает слои их высотами (один перемещается под другой). Слот для self.layers.signals.swappedLayers.
    # Используется при перемещении слоя пользователем как выше, так и ниже.
    @pyqtSlot(int, int)
    def swapLayers(self, indexA: int, indexB: int) -> None:
        aValue = self.scene.items()[indexA].zValue()
        bValue = self.scene.items()[indexB].zValue()
        self.scene.items()[indexA].setZValue(bValue)
        self.scene.items()[indexB].setZValue(aValue)

    @pyqtSlot(int, int, int)
    def addGridLine(self, direction: int, indentType: int, indent: int) -> None:
        self.scene.items()[1].widget().addLine(direction, indentType, indent)

    @pyqtSlot(int, int, int)
    def deleteGridLine(self, direction: int, indentType: int, indent: int) -> None:
        self.scene.items()[1].widget().deleteLine(direction, indentType, indent)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())
