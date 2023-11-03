import sys
import traceback
import json
import requests
from PyQt5.QtWidgets import (QApplication, QGraphicsScene, QGraphicsView, QTabWidget,
                             QWidget, QGridLayout, QShortcut, QFileDialog, QInputDialog, QMessageBox)
from PyQt5.QtGui import QFont, QKeySequence, QColor, QImage, QPainter
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


# Договорённости по именованию переменных:
# - Названия переменных пишутся в стиле camelCase, чтобы избежать смешения двух стилей (в PyQt всё пишется этим стилем)
# - Названия классов отображают, что это за класс (кнопка, превью, список, ...)
# - Названия сигналов пишутся в форме Past Participle (clicked, shown, valueChanged, ...)
# - Названия функций-слотов пишутся в форме инфинитива (addWidget, updateLayerState, swapLayers, ...)


SERVER_ADDRESS = ''


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
# - self.username
# - self.password
# - self.fileDump
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
        self.username = ''
        self.password = ''
        self.fileDump = dict()

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
        self.tab.setMaximumHeight(196)

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

        self.layers.newStaticLayer('Фон', 0)
        self.layers.newStaticLayer('Сетка', 1024)

        self.finalImage = QImage(QSize(*self.resolution), QImage.Format_ARGB32_Premultiplied)

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

    @pyqtSlot()
    def saveFile(self, variableDump=False, projectName=''):
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

        if not variableDump:
            jsonObject = json.dumps(output, indent=4)
            with open(filePath, 'w') as file:
                file.write(jsonObject)
            return

        self.fileDump = output

    def clearFile(self, width=1280, height=720):
        self.layers.clear()
        self.resolution = width, height
        self.currentLayer = -1
        self.highestZ = 0

        self.scene.addWidget(BackgroundLayer(*self.resolution))
        self.scene.addWidget(GridLayer(*self.resolution))
        self.scene.items()[-1].setZValue(1024)

        self.layers.newStaticLayer('Фон', 0)
        self.layers.newStaticLayer('Сетка', 1024)

    @pyqtSlot()
    def openFile(self, fileData=dict()):
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

        listWidgetQueue = []

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

        self.highestZ = max([i.zValue() for i in self.scene.items()[2:]] + [0])
        self.layers.deactivateAll()

        if self.currentLayer != -1:
            self.scene.items()[self.currentLayer].widget().active = False
        self.currentLayer = -1

    @pyqtSlot()
    def resizeFile(self):
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
        for item in self.scene.items():
            item.widget().setResolution(width, height, stretch)
        self.tab.widget(2).resolution = width, height
        self.tab.widget(2).sortV()
        self.tab.widget(2).sortH()

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

    @pyqtSlot(str, str, dict)
    def openCloudFile(self, username, password, projectData):
        self.loginForm.hide()
        self.changePasswordForm.hide()
        self.projectOpenForm.hide()
        self.login(username, password, dict())
        self.openFile(projectData)

    @pyqtSlot()
    def openChangePasswordForm(self):
        self.loginForm.hide()
        self.changePasswordForm.show()

    @pyqtSlot(str, str, dict)
    def login(self, username, password, projectData):
        self.username = username
        self.password = password
        self.loginForm.setLoginData(self.username, self.password)
        self.projectOpenForm.setLoginData(self.username, self.password)
        self.loginForm.hide()

    @pyqtSlot()
    def openCloudForms(self):
        self.projectOpenForm.show()
        self.loginForm.show()

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
        response = requests.post(SERVER_ADDRESS + 'save_project', data=self.fileDump).json()
        if response['status'] == 'ok':
            QMessageBox(QMessageBox.Information, 'Сохранение проекта',
                        'Проект успешно сохранен.', QMessageBox.Ok).exec()
        elif response['status'] == 'incorrectUsername':
            QMessageBox(QMessageBox.Information, 'Сохранение проекта',
                        'Введено неверное имя пользователя.', QMessageBox.Ok).exec()
        elif response['status'] == 'incorrectPassword':
            QMessageBox(QMessageBox.Information, 'Сохранение проекта',
                        'Введён неверный пароль.', QMessageBox.Ok).exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
