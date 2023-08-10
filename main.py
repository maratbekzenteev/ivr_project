import sys
from PyQt5.QtWidgets import (QApplication, QGraphicsScene, QGraphicsView, QTabWidget, QLabel,
                             QWidget, QListWidget, QPushButton, QGridLayout, QShortcut)
from PyQt5.QtGui import QPixmap, QFont, QKeySequence, QColor
from PyQt5.QtCore import Qt, QRect
from bitmap_layer import BitmapLayer
from background_layer import BackgroundLayer
from gui_classes import BitmapToolbar, LayerToolbar, LayerList


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setFont(QFont("Segoe UI", 12))

        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self.currentLayer = -1
        self.highestZ = 0
        self.resolution = 1280, 720

        self.layerList = QListWidget(self)
        self.layers = LayerList(self)
        self.preview = QGraphicsView(self)
        self.tab = QTabWidget(self)

        self.tab.addTab(BitmapToolbar(), "Рисование")
        self.tab.widget(0).signals.valueChanged.connect(self.updateLayerState)

        self.tab.addTab(LayerToolbar(), "Слои")
        self.tab.widget(1).newBitmapLayerButton.clicked.connect(self.newBitmapLayer)

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
        self.preview.setScene(self.scene)

        self.show()

    def zoomIn(self):
        self.preview.scale(1.25, 1.25)

    def zoomOut(self):
        self.preview.scale(0.8, 0.8)

    # def resizeEvent(self, event):
    #     self.layout.itemAtPosition(1, 1).widget().setGeometry(
    #         QRect(self.layout.itemAtPosition(0, 1).geometry().topLeft().x(),
    #               self.layout.itemAtPosition(1, 0).geometry().topLeft().y(),
    #               self.layout.itemAtPosition(0, 1).geometry().width(),
    #               self.layout.itemAtPosition(1, 0).geometry().height()))

    def newBitmapLayer(self):
        self.highestZ += 1
        self.scene.addWidget(BitmapLayer(*self.resolution, self))
        self.scene.items()[-1].setZValue(self.highestZ)
        self.layers.newBitmapLayer()

    def updateLayerState(self):
        if self.currentLayer != -1:
            self.scene.items()[self.currentLayer + 1].widget().updateState(self.tab.widget(0).color,
                                                                           self.tab.widget(0).width,
                                                                           self.tab.widget(0).tool)

    def activateLayer(self, index):
        if self.currentLayer != -1:
            self.scene.items()[self.currentLayer + 1].widget().active = False
        self.scene.items()[index + 1].widget().active = True
        self.currentLayer = index
        self.updateLayerState()

    def deactivateLayer(self, index):
        self.scene.items()[index + 1].widget().active = False
        self.currentLayer = -1

    def showLayer(self, index):
        self.scene.items()[index + 1].widget().show()

    def hideLayer(self, index):
        self.scene.items()[index + 1].widget().hide()

    def swapLayers(self, indexA, indexB):
        aValue = self.scene.items()[indexA + 1].zValue()
        bValue = self.scene.items()[indexB + 1].zValue()
        self.scene.items()[indexA + 1].setZValue(bValue)
        self.scene.items()[indexB + 1].setZValue(aValue)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())
