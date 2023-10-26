from PyQt5.QtWidgets import QWidget, QGridLayout, QToolButton
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize, Qt


# Виджет панели инструментов по созданию слоев. Сам по себе не сообщает сигналов, привязан к слотам в классе окна
# Графические элементы:
# - self.layout - QGridLayout, сетка выравнивания кнопок в панели
# - self.newBitmapLayerButton - QToolButton, кнопка создания растрового слоя
# - self.newShapeLayerButton - QToolButton, кнопка создания фигурного слоя
class LayerToolbar(QWidget):
    # Инициализация графических элементов
    def __init__(self):
        super().__init__()

        self.layout = QGridLayout(self)
        self.setLayout(self.layout)

        self.newBitmapLayerButton = QToolButton()
        self.newBitmapLayerButton.setText('Новый холст')
        self.newBitmapLayerButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.newBitmapLayerButton.setAutoRaise(True)
        self.newBitmapLayerButton.setIconSize(QSize(64, 64))
        self.newBitmapLayerButton.setIcon(QIcon('tmp_icon.png'))

        self.newShapeLayerButton = QToolButton()
        self.newShapeLayerButton.setText('Новый фигурный слой')
        self.newShapeLayerButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.newShapeLayerButton.setAutoRaise(True)
        self.newShapeLayerButton.setIconSize(QSize(64, 64))
        self.newShapeLayerButton.setIcon(QIcon('tmp_icon.png'))

        self.newImageLayerButton = QToolButton()
        self.newImageLayerButton.setText('Новый слой-картинка')
        self.newImageLayerButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.newImageLayerButton.setAutoRaise(True)
        self.newImageLayerButton.setIconSize(QSize(64, 64))
        self.newImageLayerButton.setIcon(QIcon('tmp_icon.png'))

        self.layout.addWidget(self.newBitmapLayerButton, 0, 0, alignment=Qt.AlignLeft)
        self.layout.addWidget(self.newShapeLayerButton, 1, 0, alignment=Qt.AlignLeft)
        self.layout.addWidget(self.newImageLayerButton, 0, 1, alignment=Qt.AlignLeft)
