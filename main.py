import sys
from PyQt5.QtWidgets import (QApplication, QGraphicsScene, QGraphicsView, QTabWidget, QLabel,
                             QWidget, QListWidget, QPushButton, QGridLayout, QShortcut)
from PyQt5.QtGui import QPixmap, QFont, QKeySequence, QColor
from PyQt5.QtCore import Qt, QRect
from bitmap_layer import BitmapLayer
from gui_classes import BitmapToolbar


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setFont(QFont("Segoe UI", 12))

        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self.currentLayer = -1
        self.highestZ = 0
        self.resolution = 1280, 720

        self.newBitmapLayerButton = QPushButton("Новый растровый слой")
        self.layerList = QListWidget(self)
        self.preview = QGraphicsView(self)
        self.tab = QTabWidget(self)

        self.tab.addTab(BitmapToolbar(), "Рисование")
        self.tab.widget(0).signals.valueChanged.connect(self.updateLayerState)

        self.layerList.currentItemChanged.connect(self.setCurrentLayer)

        self.layout.addWidget(self.newBitmapLayerButton, 0, 0)
        self.layout.addWidget(self.layerList, 1, 0)
        self.layout.addWidget(self.preview, 1, 1, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.tab, 0, 1)
        self.layout.setColumnStretch(1, 1)

        self.newBitmapLayerButton.clicked.connect(self.newBitmapLayer)

        self.zoomInShortcut = QShortcut(QKeySequence("Ctrl+="), self)
        self.zoomInShortcut.activated.connect(self.zoomIn)

        self.zoomOutShortcut = QShortcut(QKeySequence("Ctrl+-"), self)
        self.zoomOutShortcut.activated.connect(self.zoomOut)

        self.scene = QGraphicsScene(self)
        self.scene.setItemIndexMethod(-1)
        self.scene.addPixmap(QPixmap("checkerboard.png").scaled(*self.resolution, aspectRatioMode=Qt.IgnoreAspectRatio))
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
        self.layerList.addItem("Новый растровый слой")

    def updateLayerState(self):
        if self.currentLayer != -1:
            self.scene.items()[self.currentLayer + 1].widget().updateState(self.tab.widget(0).color,
                                                                           self.tab.widget(0).width,
                                                                           self.tab.widget(0).tool)

    def setCurrentLayer(self):
        if self.currentLayer != -1:
            self.scene.items()[self.currentLayer + 1].widget().active = False

        self.currentLayer = self.layerList.currentRow()
        self.preview.currentLayer = self.currentLayer
        self.scene.items()[self.currentLayer + 1].widget().active = True
        self.updateLayerState()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())
