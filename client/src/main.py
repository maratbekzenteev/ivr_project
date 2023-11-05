import sys
import json
import requests
from PyQt5.QtWidgets import (QApplication, QGraphicsScene, QGraphicsView, QTabWidget,
                             QWidget, QGridLayout, QShortcut, QFileDialog, QInputDialog, QMessageBox)
from PyQt5.QtGui import QFont, QKeySequence, QColor, QImage, QPainter, QIcon
from PyQt5.QtCore import Qt, pyqtSlot, QByteArray, QBuffer, QIODevice, QSize
from bitmapLayer import BitmapLayer
from gridLayer import GridLayer
from imageLayer import ImageLayer
from shapeLayer import ShapeLayer
from textLayer import TextLayer
from backgroundLayer import BackgroundLayer
from client.gui.bitmapToolbar import BitmapToolbar
from client.gui.imageToolbar import ImageToolbar
from client.gui.gridToolbar import GridToolbar
from client.gui.shapeToolbar import ShapeToolbar
from client.gui.textToolbar import TextToolbar
from client.gui.fileToolbar import FileToolbar
from client.gui.layerList import LayerList
from client.src.forms import LoginForm, ChangePasswordForm, ProjectOpenForm


# Договорённости по именованию переменных и комментариям:
# - Названия переменных пишутся в стиле camelCase, чтобы избежать смешения двух стилей (в PyQt всё пишется этим стилем)
# - Названия классов отображают, что это за класс (кнопка, превью, список, ...)
# - Названия сигналов пишутся в форме Past Participle (clicked, shown, valueChanged, ...)
# - Названия функций-слотов пишутся в форме инфинитива (addWidget, updateLayerState, swapLayers, ...)
# - Понятия "растровый слой" и "холст" используются взаимозаменяемо


# Адрес сервера, к которому программа подключается для получения и сохранения проектов пользователя.
# (!) Оканчивается на прямой слеш ('/')
SERVER_ADDRESS = 'http://127.0.0.1:5000/'


# Класс Window - класс главного окна программы.
# Выровнен по QGridLayout, содержит в себе (вложенно) все виджеты программы
# Графические элементы:
# - self.layout - QGridLayout, сетка выравнивания виджетов в окне
# - self.tab - QTabWidget, содержащий виджеты панелей инструментов со всем основным функционалом (см. client.gui)
# - self.preview - QGraphicsView, "рабочая область" окна. Отображает сцену self.scene
# - self.layers - LayerList (см. client.gui.layerList.py), меню управления слоями (скрытие, выделение, удаление, ...)
# - self.scene - QGraphicsScene, сцена со всеми слоями
# Атрибуты:
# - self.currentLayer - int, индекс слоя, с которым пользователь может взаимодействовать. Нумеруются с нуля (-1 - ни
# - - один слой не выделен). Слои с индексами 0 и 1 - всегда фон и сетка соответственно
# - self.highestZ - int, текущая "высота" самого высокого слоя. Поддерживается также в LayerList
# - self.resolution - tuple(int, int), разрешение целевого изображения проекта
# - self.username - str, имя пользователя на сервере. Задаётся через self.loginForm или self.changePasswordForm
# - self.password - str, пароль пользователся на сервере. Задаётся через self.loginForm или self.changePasswordForm
# - self.fileDump - dict, JSON-словарь, содержащий в себе всю информацию о проекте. Содержимое передаётся в запросе
# - - серверу при сохранении туда проекта. Подробности о формате см. в self.saveFile
# - self.finalImage - QImage, картинка, на которой отрисовывается содержимое всех слоёв, кроме фона и сетки, перед
# - - сохранением непосредственно на компьютер
class Window(QWidget):
    # Инициализация графических элементов и атрибутов, подключение сигналов к слотам
    def __init__(self) -> None:
        super().__init__()
        self.setFont(QFont('Verdana', 12))
        self.setWindowTitle('Grid Raster Image Editor')
        self.setWindowIcon(QIcon('../static/pen3.png'))

        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self.currentLayer = -1
        self.highestZ = 0
        self.resolution = 1280, 720
        self.username = ''
        self.password = ''
        self.fileDump = dict()
        self.finalImage = QImage(QSize(*self.resolution), QImage.Format_ARGB32_Premultiplied)

        # Комбинации клавиш для быстрой работы в программе
        self.zoomInShortcut = QShortcut(QKeySequence("Ctrl+="), self)
        self.zoomInShortcut.activated.connect(self.zoomIn)
        self.zoomOutShortcut = QShortcut(QKeySequence("Ctrl+-"), self)
        self.zoomOutShortcut.activated.connect(self.zoomOut)

        self.loginForm = LoginForm(SERVER_ADDRESS)
        self.loginForm.signals.requestAccepted.connect(self.login)
        self.loginForm.signals.openForm.connect(self.openChangePasswordForm)
        self.changePasswordForm = ChangePasswordForm(SERVER_ADDRESS)
        self.changePasswordForm.signals.requestAccepted.connect(self.login)
        self.projectOpenForm = ProjectOpenForm(SERVER_ADDRESS)
        self.projectOpenForm.signals.requestAccepted.connect(self.openCloudFile)

        self.layers = LayerList(self)
        self.preview = QGraphicsView(self)
        self.tab = QTabWidget(self)
        self.tab.setMaximumHeight(240)

        self.tab.addTab(BitmapToolbar(), "Холст")
        self.tab.widget(0).signals.valueChanged.connect(self.updateBitmapLayerState)

        self.tab.addTab(FileToolbar(), "Файл")
        self.tab.widget(1).saveButton.clicked.connect(self.saveFile)
        self.tab.widget(1).openButton.clicked.connect(self.openFile)
        self.tab.widget(1).resizeButton.clicked.connect(self.resizeFile)
        self.tab.widget(1).newButton.clicked.connect(self.newFile)
        self.tab.widget(1).exportButton.clicked.connect(self.exportFile)
        self.tab.widget(1).cloudOpenButton.clicked.connect(self.openCloudForms)
        self.tab.widget(1).cloudSaveButton.clicked.connect(self.saveCloudFile)

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

        self.setTabsInvisible()

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

        self.scene = QGraphicsScene(self)
        self.scene.setItemIndexMethod(-1)
        self.scene.addWidget(BackgroundLayer(*self.resolution))
        self.scene.addWidget(GridLayer(*self.resolution))
        self.scene.items()[-1].setZValue(1024)
        self.preview.setScene(self.scene)

        self.layers.newStaticLayer('Фон', 0)
        self.layers.newStaticLayer('Сетка', 1024)

        self.show()

    # Функция скрытия всех вкладок работы со слоями. Вызывается, когда работа ни с одним типом слоёв невозможна,
    # (например, когда ни один слой не активен)
    def setTabsInvisible(self) -> None:
        self.tab.setTabVisible(0, False)
        self.tab.setTabVisible(3, False)
        self.tab.setTabVisible(4, False)
        self.tab.setTabVisible(5, False)

    # Слот для self.zoomInShortcut, увеличивает масштаб отображения в рабочей области в 5/4 раза
    @pyqtSlot()
    def zoomIn(self) -> None:
        self.preview.scale(1.25, 1.25)

    # Слот для self.zoomOutShortcut, увеличивает масштаб отображения в рабочей области в 4/5 раза
    @pyqtSlot()
    def zoomOut(self) -> None:
        self.preview.scale(0.8, 0.8)

    # Добавление нового растрового слоя.
    # Слот сигнала self.layers.newBitmapButton.clicked, увеличивает макс. высоту слоя,
    # добавляет слой на сцену (как и любой слой, в виде QProxyWidget) и в список слоёв.
    @pyqtSlot()
    def addBitmapLayer(self) -> None:
        self.highestZ += 1
        self.scene.addWidget(BitmapLayer(*self.resolution, self))
        self.scene.items()[-1].setZValue(self.highestZ)
        self.layers.newBitmapLayer()

    # Добавление нового слоя-картинки.
    # Слот сигнала self.layers.newImageButton.clicked, увеличивает макс. высоту слоя,
    # добавляет слой на сцену (как и любой слой, в виде QProxyWidget) и в список слоёв.
    @pyqtSlot()
    def addImageLayer(self) -> None:
        self.highestZ += 1
        self.scene.addWidget(ImageLayer('tmp_icon.png', *self.resolution, self))
        self.scene.items()[-1].setZValue(self.highestZ)
        self.layers.newImageLayer()

    # Добавление нового фигурного слоя.
    # Слот сигнала self.layers.newShapeButton.clicked, увеличивает макс. высоту слоя,
    # добавляет слой на сцену (как и любой слой, в виде QProxyWidget) и в список слоёв.
    @pyqtSlot()
    def addShapeLayer(self) -> None:
        self.highestZ += 1
        self.scene.addWidget(ShapeLayer(*self.resolution, self))
        self.scene.items()[-1].setZValue(self.highestZ)
        self.layers.newShapeLayer()

    # Добавление нового текстового слоя.
    # Слот сигнала self.layers.newTextButton.clicked, увеличивает макс. высоту слоя,
    # добавляет слой на сцену (как и любой слой, в виде QProxyWidget) и в список слоёв.
    @pyqtSlot()
    def addTextLayer(self) -> None:
        self.highestZ += 1
        self.scene.addWidget(TextLayer(*self.resolution, self))
        self.scene.items()[-1].setZValue(self.highestZ)
        self.layers.newTextLayer()

    # Обновление состояния выделенного растрового слоя при изменении состояния панели инструментов пользователем.
    # Слот сигнала self.tab.widget(0).valueChanged
    @pyqtSlot()
    def updateBitmapLayerState(self) -> None:
        if self.currentLayer != -1 and isinstance(self.scene.items()[self.currentLayer].widget(), BitmapLayer):
            self.scene.items()[self.currentLayer].widget().updateState(self.tab.widget(0).color,
                                                                           self.tab.widget(0).width,
                                                                           self.tab.widget(0).tool)

    # Обновление состояния выделенного слоя-картинки при изменении состояния панели инструментов пользователем.
    # Слот сигнала self.tab.widget(3).stateChanged
    @pyqtSlot(int, str, str)
    def updateImageLayerState(self, size: int, alignment: str, tool: str) -> None:
        if self.currentLayer != -1 and isinstance(self.scene.items()[self.currentLayer].widget(), ImageLayer):
            self.scene.items()[self.currentLayer].widget().updateState(size, alignment, tool)

    # Обновление картинки выделенного слоя-картинки при выборе пользователем новой картинки при помощи панели
    # инструментов. Слот сигнала self.tab.widget(3).imageChanged
    @pyqtSlot(str)
    def updateImageLayerImage(self, imagePath):
        if self.currentLayer != -1 and isinstance(self.scene.items()[self.currentLayer].widget(), ImageLayer):
            self.scene.items()[self.currentLayer].widget().updateImage(imagePath)

    # Обновление панели инструментов ImageToolbar до состояния текущего слоя-картинки. Вызывается при повторном
    # выделении слоя-картинки, чтобы на панели инструментов отображались данные именно о нём
    def updateImageToolbarState(self):
        self.tab.widget(3).filePath = self.scene.items()[self.currentLayer].widget().imagePath
        self.tab.widget(3).size = self.scene.items()[self.currentLayer].widget().size
        self.tab.widget(3).alignmentSelector.setState(self.scene.items()[self.currentLayer].widget().alignment)
        self.tab.widget(3).toolSelector.setState(self.scene.items()[self.currentLayer].widget().tool)

    # Обновление состояния выделенного фигурного слоя при изменении состояния панели инструментов пользователем.
    # Слот сигнала self.tab.widget(4).valueChanged
    @pyqtSlot()
    def updateShapeLayerState(self):
        if self.currentLayer != -1 and isinstance(self.scene.items()[self.currentLayer].widget(), ShapeLayer):
            self.scene.items()[self.currentLayer].widget().updateState(self.tab.widget(4).lineColor,
                                                                       self.tab.widget(4).fillColor,
                                                                       self.tab.widget(4).width,
                                                                       self.tab.widget(4).tool,
                                                                       self.tab.widget(4).shape)

    # Обновление панели инструментов ShapeToolbar до состояния текущего фигурного слоя. Вызывается при повторном
    # выделении фигурного слоя, чтобы на панели инструментов отображались данные именно о нём
    def updateShapeToolbarState(self):
        self.tab.widget(4).setState(self.scene.items()[self.currentLayer].widget().lineColor,
                                    self.scene.items()[self.currentLayer].widget().fillColor,
                                    self.scene.items()[self.currentLayer].widget().width,
                                    self.scene.items()[self.currentLayer].widget().tool,
                                    self.scene.items()[self.currentLayer].widget().shape)

    # Обновление состояния выделенного текстового слоя при изменении состояния панели инструментов пользователем.
    # Слот сигнала self.tab.widget(5).valueChanged
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

    # Обновление панели инструментов TextToolbar до состояния текущего текстового слоя. Вызывается при повторном
    # выделении текстового слоя, чтобы на панели инструментов отображались данные именно о нём
    def updateTextToolbarState(self):
        self.tab.widget(5).setState(self.scene.items()[self.currentLayer].widget().color,
                                    self.scene.items()[self.currentLayer].widget().font,
                                    self.scene.items()[self.currentLayer].widget().size,
                                    self.scene.items()[self.currentLayer].widget().fontWeight,
                                    self.scene.items()[self.currentLayer].widget().italic,
                                    self.scene.items()[self.currentLayer].widget().underline,
                                    self.scene.items()[self.currentLayer].widget().alignment)

    # Активация слоя по индексу. Слот для self.layers.signals.activated.
    # Снимает выделение с ранее выделенного слоя (если таковой был), делает активным текущий выделенный слой,
    # передаёт состояние панели инструментов на случай, если её состояние поменяли, пока активным был другой слой,
    # обновляет переменную self.currentLayer. Обновляет состояние доступных вкладок
    @pyqtSlot(int)
    def activateLayer(self, index: int) -> None:
        if self.currentLayer != -1:
            self.scene.items()[self.currentLayer].widget().active = False
            if isinstance(self.scene.items()[self.currentLayer].widget(), TextLayer):
                self.scene.items()[self.currentLayer].setZValue(self.scene.items()[self.currentLayer].widget()
                                                                .previousZValue)

        self.scene.items()[index].widget().active = True
        self.currentLayer = index
        self.setTabsInvisible()

        if isinstance(self.scene.items()[self.currentLayer].widget(), BitmapLayer):
            self.tab.setTabVisible(0, True)
            self.tab.setCurrentIndex(0)
            self.updateBitmapLayerState()
        elif isinstance(self.scene.items()[self.currentLayer].widget(), ImageLayer):
            self.tab.setTabVisible(3, True)
            self.tab.setCurrentIndex(3)
            self.updateImageToolbarState()
        elif isinstance(self.scene.items()[self.currentLayer].widget(), ShapeLayer):
            self.tab.setTabVisible(4, True)
            self.tab.setCurrentIndex(4)
            self.updateShapeToolbarState()
        elif isinstance(self.scene.items()[self.currentLayer].widget(), TextLayer):
            self.tab.setTabVisible(5, True)
            self.tab.setCurrentIndex(5)
            self.scene.items()[self.currentLayer].widget().storeZValue(self.scene.items()[self.currentLayer].zValue())
            self.scene.items()[self.currentLayer].setZValue(1023)
            self.updateTextToolbarState()

    # Деактивация слоя по индексу. Слот для self.layers.signals.deactivated.
    # Снимает выделение с ранее выделенного слоя (который и послал сигнал),
    # сообщает в self.currentLayer, что никакой слой не выделен.
    @pyqtSlot(int)
    def deactivateLayer(self, index: int) -> None:
        if isinstance(self.scene.items()[self.currentLayer].widget(), TextLayer):
            self.scene.items()[self.currentLayer].setZValue(self.scene.items()[self.currentLayer].widget()
                                                            .previousZValue)

        self.tab.setCurrentIndex(1)
        self.setTabsInvisible()
        self.scene.items()[index].widget().active = False
        self.currentLayer = -1

    # Показывает слой по индексу. Слот для self.layers.signals.shown
    @pyqtSlot(int)
    def showLayer(self, index: int) -> None:
        self.scene.items()[index].widget().show()

    # Скрытие слоя по индексу. Слот для self.layers.signals.hidden
    @pyqtSlot(int)
    def hideLayer(self, index: int) -> None:
        self.scene.items()[index].widget().hide()

    # Удаление слоя по индексу. Слот для self.layers.signals.deleted
    @pyqtSlot(int)
    def deleteLayer(self, index):
        if self.currentLayer == index:
            self.tab.setCurrentIndex(1)
            self.setTabsInvisible()

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

    # Добавление линии сетки. Подробнее о формате direction, indentType, indent см. в client.gui.gridToolbar.py или
    # client.src.gridLayer.py
    @pyqtSlot(int, int, int)
    def addGridLine(self, direction: int, indentType: int, indent: int) -> None:
        self.scene.items()[1].widget().addLine(direction, indentType, indent)

    # Удаление линии сетки. Подробнее о формате direction, indentType, indent см. в client.gui.gridToolbar.py или
    # client.src.gridLayer.py
    @pyqtSlot(int, int, int)
    def deleteGridLine(self, direction: int, indentType: int, indent: int) -> None:
        self.scene.items()[1].widget().deleteLine(direction, indentType, indent)

    # Сохранение проекта. Содержимое проекта записывается в output (протокол см. ниже).
    # Если variableDump верно, то содержимое output копируется в self.fileDump для последующей
    # передачи на сервер в JSON части запроса для сохранения проекта на сервере, иначе записывается в файл на
    # компьютере пользователя (путь и имя файла спрашиваются у пользователся через диалог).
    # Слот сигнала FileToolbar.saveButton.clicked
    # Протокол описания проекта (в нотации JSON):
    # - name - str, имя проекта
    # - width - int, ширина выходного изображения проекта
    # - height - int, высота выходного изображения проекта
    # - highestZ - int, см. self.highestZ
    # - layers - list, в котором содержится разная информация о слое в зависимости от его типа:
    # - - О BackgroundLayer информация не записывается
    # - - О BitmapLayer:
    # - - - type = 'bmp'
    # - - - data - str, строковое utf-8 представление потока байтов, полученного из BitmapLayer.bitmap
    # - - - z - целочисленный float, высота слоя
    # - - - index - int, индекс в self.scene
    # - - - name - str, название слоя, данное пользователем в списке слоёв
    # - - Об ImageLayer:
    # - - - type = 'img'
    # - - - data - str, строковое utf-8 представление потока байтов, полученного из ImageLayer.image
    # - - - xOffset - int, отступ по горизонтали в пикселях от точки, где картинка должна лежать идеально по сетке
    # - - - yOffset - int, отступ по вертикали в пикселях от точки, где картинка должна лежать идеально по сетке
    # - - - alignment - str, выравниваение текущего слоя-картинки по сетке. Подробнее см. в client.src.imageLayer.py
    # - - - leftBorder - tuple(int, int), левая сторона прямоугольника, подробнее см. в imageLayer.py
    # - - - rightBorder - tuple(int, int), правая сторона прямоугольника, подробнее см. в imageLayer.py
    # - - - topBorder - tuple(int, int), верхняя сторона прямоугольника, подробнее см. в imageLayer.py
    # - - - bottomBorder - tuple(int, int), нижняя сторона прямоугольника, подробнее см. в imageLayer.py
    # - - - size - int, масштаб, в котором картинка отображается (в процентах от фактического размера)
    # - - - z - целочисленный float, высота слоя
    # - - - index - int, индекс в self.scene
    # - - - name - str, название слоя, данное пользователем в списке слоёв
    # - - О ShapeLayer:
    # - - - type = 'shp'
    # - - - shape - str, тип фигуры ('none', 'line', 'oval', 'rect')
    # - - - xOffset - int, отступ по горизонтали в пикселях от точки, где фигура должна лежать идеально по сетке
    # - - - yOffset - int, отступ по вертикали в пикселях от точки, где фигура должна лежать идеально по сетке
    # - - - width - int, толщина обводки фигуры
    # - - - lineColor - tuple(int, int, int, int), цвет обводки, задаётся в порядке red, green, blue, alpha
    # - - - fillColor - tuple(int, int, int, int), цвет заливки, задаётся в порядке red, green, blue, alpha
    # - - - firstVBorder - tuple(int, int), 1-я вертикальная ограничивающая линия, подробнее см. в imageLayer.py
    # - - - firstHBorder - tuple(int, int), 1-я горизонтальная ограничивающая линия, подробнее см. в imageLayer.py
    # - - - secondVBorder - tuple(int, int), 2-я вертикальная ограничивающая линия, подробнее см. в imageLayer.py
    # - - - secondHBorder - tuple(int, int), 2-я горизонтальная ограничивающая линия, подробнее см. в imageLayer.py
    # - - - z - целочисленный float, высота слоя
    # - - - index - int, индекс в self.scene
    # - - - name - str, название слоя, данное пользователем в списке слоёв
    # - - О TextLayer:
    # - - - type = 'txt'
    # - - - text - str, текст надписи, представленный в формате HTML
    # - - - leftBorder - tuple(int, int), левая сторона прямоугольника, подробнее см. в imageLayer.py
    # - - - rightBorder - tuple(int, int), правая сторона прямоугольника, подробнее см. в imageLayer.py
    # - - - topBorder - tuple(int, int), верхняя сторона прямоугольника, подробнее см. в imageLayer.py
    # - - - bottomBorder - tuple(int, int), нижняя сторона прямоугольника, подробнее см. в imageLayer.py
    # - - - z - целочисленный float, высота слоя
    # - - - index - int, индекс в self.scene
    # - - - name - str, название слоя, данное пользователем в списке слоёв
    # - - О GridLayer:
    # - - - type = 'grd'
    # - - - h - list(tuple(int, int)), список горизонтальных линий сетки, о формате см. client.src.gridLayer.py
    # - - - v - list(tuple(int, int)), список вертикальных линий сетки, о формате см. client.src.gridLayer.py
    # - - - z=1024.0
    # - - - index - int, индекс в self.scene
    # - - - name - str, название слоя в списке слоёв
    @pyqtSlot()
    def saveFile(self, variableDump=False, projectName='') -> None:
        filePath = ''
        if projectName == '':
            filePath = QFileDialog.getSaveFileName(self, 'Сохранить проект', filter='Файл проекта GrImage (*.gri)')[0]
            if filePath == '':
                return

        self.layers.deactivateAll()
        if self.currentLayer != -1:
            if isinstance(self.scene.items()[self.currentLayer].widget(), TextLayer):
                self.scene.items()[self.currentLayer].setZValue(self.scene.items()[self.currentLayer].widget()
                                                                .previousZValue)

            self.scene.items()[self.currentLayer].widget().active = False
            self.currentLayer = -1

        output = {}
        output['name'] = '.'.join(filePath.split('/')[-1].split('.')[:-1]) if projectName == '' else projectName
        output['width'], output['height'] = self.resolution
        output['highestZ'] = self.highestZ
        output['layers'] = []

        for i in range(len(self.scene.items())):
            curWidget = self.scene.items()[i].widget()

            if isinstance(curWidget, BitmapLayer):
                byteArray = QByteArray()
                buffer = QBuffer(byteArray)
                buffer.open(QIODevice.WriteOnly)
                self.scene.items()[i].widget().bitmap.save(buffer, "PNG")
                buffer.close()
                output['layers'].append({
                    'type': 'bmp',
                    'data': str(byteArray.toBase64(), 'utf_8')
                })
            elif isinstance(self.scene.items()[i].widget(), ImageLayer):
                byteArray = QByteArray()
                buffer = QBuffer(byteArray)
                buffer.open(QIODevice.WriteOnly)
                self.scene.items()[i].widget().image.save(buffer, "PNG")
                buffer.close()
                output['layers'].append({
                    'type': 'img',
                    'data': str(byteArray.toBase64(), 'utf_8'),
                    'xOffset': curWidget.xOffset,
                    'yOffset': curWidget.yOffset,
                    'alignment': curWidget.alignment,
                    'leftBorder': curWidget.leftBorder,
                    'rightBorder': curWidget.rightBorder,
                    'topBorder': curWidget.topBorder,
                    'bottomBorder': curWidget.bottomBorder,
                    'size': curWidget.size
                })
            elif isinstance(self.scene.items()[i].widget(), ShapeLayer):
                output['layers'].append({
                    'type': 'shp',
                    'shape': curWidget.shape,
                    'xOffset': curWidget.xOffset,
                    'yOffset': curWidget.yOffset,
                    'width': curWidget.width,
                    'lineColor': (curWidget.lineColor.red(), curWidget.lineColor.green(), curWidget.lineColor.blue(),
                                  curWidget.lineColor.alpha()),
                    'fillColor': (curWidget.fillColor.red(), curWidget.fillColor.green(), curWidget.fillColor.blue(),
                                  curWidget.fillColor.alpha()),
                    'firstVBorder': curWidget.firstVBorder,
                    'firstHBorder': curWidget.firstHBorder,
                    'secondVBorder': curWidget.secondVBorder,
                    'secondHBorder': curWidget.secondHBorder,
                })
            elif isinstance(self.scene.items()[i].widget(), TextLayer):
                output['layers'].append({
                    'type': 'txt',
                    'text': curWidget.textEdit.toHtml(),
                    'leftBorder': curWidget.leftBorder,
                    'rightBorder': curWidget.rightBorder,
                    'topBorder': curWidget.topBorder,
                    'bottomBorder': curWidget.bottomBorder
                })
            elif isinstance(self.scene.items()[i].widget(), GridLayer):
                output['layers'].append({
                    'type': 'grd',
                    'h': curWidget.hLines,
                    'v': curWidget.vLines
                })

            if not isinstance(curWidget, BackgroundLayer):
                output['layers'][-1]['z'] = self.scene.items()[i].zValue()
                output['layers'][-1]['name'] = self.layers.getName(i)
                output['layers'][-1]['index'] = i

        # Объект записывается в файл, если это требуется
        if not variableDump:
            jsonObject = json.dumps(output, indent=4)
            with open(filePath, 'w') as file:
                file.write(jsonObject)
            return

        self.fileDump = output

    # Очистка проекта с заданием нового разрешения. Очищается в т.ч. список слоёв и сцена.
    # Вызывается при открытии проекта или создании нового
    def clearFile(self, width=1280, height=720) -> None:
        self.layers.clear()
        self.resolution = width, height
        self.currentLayer = -1
        self.highestZ = 0

        self.scene.addWidget(BackgroundLayer(*self.resolution))
        self.scene.addWidget(GridLayer(*self.resolution))
        self.scene.items()[-1].setZValue(1024)

        self.layers.newStaticLayer('Фон', 0)
        self.layers.newStaticLayer('Сетка', 1024)

    # Открытие проекта. Если в fileData что-то передано (когда проект открывается с сервера),
    # то открытие происходит оттуда, иначе пользователь выбирает файл на компьютере, который нужно открыть. Формат файла
    # идентичен описанному в self.saveFile. Слот сигнала FileToolbar.openButton.clicked
    @pyqtSlot()
    def openFile(self, fileData=dict()) -> None:
        if fileData == dict():
            filePath = QFileDialog.getOpenFileName(self, 'Открыть файл проекта', '', 'Файл проекта GrImage (*.gri)')[0]
            if filePath == '':
                return

            with open(filePath, 'r') as file:
                jsonObject = json.load(file)
        else:
            jsonObject = fileData

        width, height = jsonObject['width'], jsonObject['height']
        self.clearFile(width=width, height=height)

        # Очередь, в которой слои будут добавлены в список слоёв
        listWidgetQueue = []

        # Слои восстанавливаются на сцене в порядке индексов
        for layer in jsonObject['layers']:
            if layer['type'] == 'grd':
                self.scene.items()[-1].widget().hLines = list(layer['h'])
                self.scene.items()[-1].widget().vLines = list(layer['v'])
            elif layer['type'] == 'bmp':
                self.scene.addWidget(BitmapLayer(*self.resolution, self))
                self.scene.items()[-1].setZValue(layer['z'])
                byteArray = QByteArray.fromBase64(bytes(layer['data'], 'utf-8'))
                self.scene.items()[-1].widget().bitmap.loadFromData(byteArray)
                # self.layers.newBitmapLayer()
                listWidgetQueue.append((layer['z'], layer['index'], layer['type'], layer['name']))
            elif layer['type'] == 'img':
                self.scene.addWidget(ImageLayer('tmp_icon.png', *self.resolution, self))
                self.scene.items()[-1].setZValue(layer['z'])
                byteArray = QByteArray.fromBase64(bytes(layer['data'], 'utf-8'))
                self.scene.items()[-1].widget().image.loadFromData(byteArray)
                self.scene.items()[-1].widget().xOffset = layer['xOffset']
                self.scene.items()[-1].widget().yOffset = layer['yOffset']
                self.scene.items()[-1].widget().alignment = layer['alignment']
                self.scene.items()[-1].widget().leftBorder = tuple(layer['leftBorder'])
                self.scene.items()[-1].widget().rightBorder = tuple(layer['rightBorder'])
                self.scene.items()[-1].widget().topBorder = tuple(layer['topBorder'])
                self.scene.items()[-1].widget().bottomBorder = tuple(layer['bottomBorder'])
                self.scene.items()[-1].widget().size = layer['size']
                # self.layers.newImageLayer()
                listWidgetQueue.append((layer['z'], layer['index'], layer['type'], layer['name']))
            elif layer['type'] == 'shp':
                self.scene.addWidget(ShapeLayer(*self.resolution, self))
                self.scene.items()[-1].setZValue(layer['z'])
                self.scene.items()[-1].widget().shape = layer['shape']
                self.scene.items()[-1].widget().xOffset = layer['xOffset']
                self.scene.items()[-1].widget().yOffset = layer['yOffset']
                self.scene.items()[-1].widget().width = layer['width']
                self.scene.items()[-1].widget().lineColor = QColor(layer['lineColor'][0], layer['lineColor'][1],
                                                                   layer['lineColor'][2], alpha=layer['lineColor'][3])
                self.scene.items()[-1].widget().fillColor = QColor(layer['fillColor'][0], layer['fillColor'][1],
                                                                   layer['fillColor'][2], alpha=layer['fillColor'][3])
                self.scene.items()[-1].widget().firstVBorder = layer['firstVBorder']
                self.scene.items()[-1].widget().firstHBorder = layer['firstHBorder']
                self.scene.items()[-1].widget().secondVBorder = layer['secondVBorder']
                self.scene.items()[-1].widget().secondHBorder = layer['secondHBorder']
                # self.layers.newShapeLayer()
                listWidgetQueue.append((layer['z'], layer['index'], layer['type'], layer['name']))
            elif layer['type'] == 'txt':
                self.scene.addWidget(TextLayer(*self.resolution, self))
                self.scene.items()[-1].setZValue(layer['z'])
                self.scene.items()[-1].widget().textEdit.setHtml(layer['text'])
                self.scene.items()[-1].widget().leftBorder = tuple(layer['leftBorder'])
                self.scene.items()[-1].widget().rightBorder = tuple(layer['rightBorder'])
                self.scene.items()[-1].widget().topBorder = tuple(layer['topBorder'])
                self.scene.items()[-1].widget().bottomBorder = tuple(layer['bottomBorder'])
                self.scene.items()[-1].widget().updateTextEdit()
                # self.layers.newTextLayer()
                listWidgetQueue.append((layer['z'], layer['index'], layer['type'], layer['name']))

        # В список слоёв слои добавляются в порядке высот, а не индексов
        listWidgetQueue.sort()
        for (z, index, layerType, name) in listWidgetQueue:
            if layerType == 'bmp':
                self.layers.newBitmapLayer(z, index, name)
            elif layerType == 'img':
                self.layers.newImageLayer(z, index, name)
            elif layerType == 'shp':
                self.layers.newShapeLayer(z, index, name)
            elif layerType == 'txt':
                self.layers.newTextLayer(z, index, name)

        # Максимальная высота восстанавливается из файла
        self.highestZ = max([i.zValue() for i in self.scene.items()[2:]] + [0])
        self.layers.deactivateAll()

        if self.currentLayer != -1:
            self.scene.items()[self.currentLayer].widget().active = False
        self.currentLayer = -1

    # Изменение разрешения проекта. Слот сигнала FileToolbar.resizeButton.clicked. Повторная сортировка нужна,
    # чтобы правильно друг относительно друга располагались относительно и абсолютно заданные линии сетки
    @pyqtSlot()
    def resizeFile(self) -> None:
        width = QInputDialog.getInt(self, 'Ширина изображения', 'Укажите желаемую ширину изображения.', 1280, min=1)
        if width[1] is False:
            return
        height = QInputDialog.getInt(self, 'Высота изображения', 'Укажите желаемую высоту изображения.', 720, min=1)
        if height[1] is False:
            return
        stretch = True if \
            QMessageBox.question(self, 'Масштабирование холстов',
                                 'Желаете ли вы, чтобы холсты растянулись/сжались после изменения размера?') == \
            QMessageBox.Yes else False
        width, height = width[0], height[0]
        self.resolution = width, height
        for item in self.scene.items():
            item.widget().setResolution(width, height, stretch)
        self.tab.widget(2).resolution = width, height
        self.tab.widget(2).sortV()
        self.tab.widget(2).sortH()

    # Создание нового проекта с разрешением, указанным пользователем в диалогах.
    # Слот сигнала FileToolbar.newButton.clicked
    @pyqtSlot()
    def newFile(self):
        width = QInputDialog.getInt(self, 'Ширина изображения', 'Укажите желаемую ширину изображения.', 1280, min=1)
        if width[1] is False:
            return
        height = QInputDialog.getInt(self, 'Высота изображения', 'Укажите желаемую высоту изображения.', 720, min=1)
        if height[1] is False:
            return
        width, height = width[0], height[0]
        self.clearFile(width=width, height=height)

    # Экспорт проекта в файл. Сначала все слои деактивируются, чтобы не отображались вспомогательные элементы.
    # Затем содержимое слоёв отрисовывается на self.finalImage, потом self.finalImage сохраняется в файл нужного формата
    # Слот сигнала FileToolbar.exportButton.clicked
    @pyqtSlot()
    def exportFile(self):
        filePath = QFileDialog.getSaveFileName(self, 'Экспорт проекта в изображение',
                                               filter='''Portable Network Graphics (*.png);;
                                                      Bitmap Picture (*.bmp);;
                                                      Joint Photographic Experts Group (*.jpg)''')[0]
        if filePath == '':
            return

        self.layers.deactivateAll()
        if self.currentLayer != -1:
            self.scene.items()[self.currentLayer].widget().active = False
        self.currentLayer = -1

        self.finalImage = QImage(QSize(*self.resolution), QImage.Format_ARGB32_Premultiplied)
        self.finalImage.fill(QColor(0, 0, 0, alpha=0))
        qp = QPainter(self.finalImage)
        for item in sorted(self.scene.items()[2:], key=lambda x: x.zValue()):
            item.widget().render(qp)
        self.finalImage.save(filePath)

    # Слот сигнала self.projectOpenForm.signals.requestAccepted. Скрывает все формы, открывает проект
    @pyqtSlot(str, str, dict)
    def openCloudFile(self, username: str, password: str, projectData: dict):
        self.loginForm.hide()
        self.changePasswordForm.hide()
        self.projectOpenForm.hide()
        self.login(username, password, dict())
        self.openFile(projectData)

    # Слот сигнала self.LoginForm.signals.openForm. Перенаправяет пользователя в форму ChangePasswordForm
    @pyqtSlot()
    def openChangePasswordForm(self):
        self.loginForm.hide()
        self.changePasswordForm.show()

    # Слот сигнала self.signals.loginForm.requestAccepted. Запоминает данные, по которым удалось войти, обновляет форму
    # self.projectOpenForm
    @pyqtSlot(str, str, dict)
    def login(self, username: str, password: str, projectData: dict):
        self.username = username
        self.password = password
        self.loginForm.setLoginData(self.username, self.password)
        self.projectOpenForm.setLoginData(self.username, self.password)
        self.loginForm.hide()

    # Слот сигнала FileToolbar.cloudOpenButton.clicked. Открывает формы для входа и выбора файла
    @pyqtSlot()
    def openCloudForms(self):
        self.projectOpenForm.show()
        self.loginForm.show()

    # Слот сигнала FileToolbar.cloudSaveButton.clicked. Спрашивает у пользователся имя проекта и отправляет запрос на
    # сохранение, уведомляет пользователя о результате через модальные диалоги
    @pyqtSlot()
    def saveCloudFile(self):
        if self.username == '':
            self.loginForm.show()
            return

        projectName = QInputDialog.getText(self, 'Сохранение проекта в облаке', 'Укажите имя проекта')[0]
        if projectName == '':
            return
        self.saveFile(variableDump=True, projectName=projectName)
        self.fileDump['username'] = self.username
        self.fileDump['password'] = self.password
        response = requests.post(SERVER_ADDRESS + 'save_project', json=self.fileDump).json()
        if response['status'] == 'ok':
            QMessageBox(QMessageBox.Information, 'Сохранение проекта',
                        'Проект успешно сохранен.', QMessageBox.Ok).exec()
        elif response['status'] == 'incorrectUsername':
            QMessageBox(QMessageBox.Information, 'Сохранение проекта',
                        'Введено неверное имя пользователя.', QMessageBox.Ok).exec()
        elif response['status'] == 'incorrectPassword':
            QMessageBox(QMessageBox.Information, 'Сохранение проекта',
                        'Введён неверный пароль.', QMessageBox.Ok).exec()


# Запуск программы
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
