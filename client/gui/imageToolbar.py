from PyQt5.QtWidgets import QWidget, QGridLayout, QSlider, QFileDialog, QToolButton
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot, Qt, QSize
from client.src.signals import ImageSignals
from client.gui.toolSelector import ToolSelector
from client.gui.widthPictogram import WidthPictogram


# Виджет панели инструментов для манипуляций со слоем-картинкой. Набор сигналов - ImageSignals.
# Графические элементы:
# - self.layout - QGridLayout, сетка выравнивания элементов панели
# - self.alignmentSelector - ToolSelector, определяет выравниваение текущего слоя-картинки относительно сетки. Значения:
# - - 'fill' - растягивается на весь прямоугольник из линий сетки, в котором лежит (далее - "прямоугольник")
# - - 'lt' - лежит в левом верхнем углу прямоугольника
# - - 'top' - лежит внутри прямоугольника посередине его верхней стороны
# - - 'rt' - лежит в правом верхмем углу прямоугольника
# - - 'left' - лежит внутри прямоугольника посередине его левой стороны
# - - 'cntr' - лежит по центру прямоугольника
# - - 'rght' - лежит внутри прямоугольника посередине его правой стороны
# - - 'lb' - лежит в левом нижнем углу прямоугольника
# - - 'bttm' - лежит внутри прямоугольника посередине его нижней грани
# - - 'rb' - лежит в правом нижнем углу прямоугольника
# - self.toolSelector - ToolSelector, определяет текущий метод работы с текущим слоем-картинкой. Состояния:
# - - 'none' - никакой инструмент не выбран
# - - 'grid' - выбирается прямоугольник из линий сетки, в котором картинка лежит
# - - 'ofst' - задается отступ - "оффсет" - в пикселях от точки, где картинка должна лежать идеально по сетке
# - self.sizeSlider - QSlider, позволяет пользователю выбрать масштаб, в котором картинка отображается (в процентах
# - от фактического размера)
# - self.selectFileButton - QToolButton, позволяет пользователю выбрать картинку, которая будет отображатся на слое
# Атрибуты:
# - self.size - int, принимает целые значения из [0;200], определяет масштам, в котором картинка отображается в
# - - изображении в проекте (в процентах от фактического разрешения)
# - self.filePath - str, задаёт путь до картинки, которая отображается на слое (если файл проекта не создан с нуля,
# - - а открыт из gri-файла, то данные о картинке будут загружены оттуда)
class ImageToolbar(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self.signals = ImageSignals()

        self.alignmentSelector = ToolSelector('Заполнить', 'Слева сверху', 'Сверху', 'Справа сверху', 'Слева',
                                              'По центру', 'Справа', 'Слева снизу', 'Снизу', 'Справа снизу')
        self.alignmentSelector.setStates('fill', 'lt', 'top', 'rt', 'left', 'cntr', 'rght', 'lb', 'bttm', 'rb')
        self.alignmentSelector.setIcons(*(['tmp_icon.png'] * 10))
        self.alignmentSelector.signals.valueChanged.connect(self.updateValues)

        self.toolSelector = ToolSelector('Привязать', 'Передвинуть')
        self.toolSelector.setStates('grid', 'ofst')
        self.toolSelector.setIcons(*(['tmp_icon.png'] * 2))
        self.toolSelector.signals.valueChanged.connect(self.updateValues)

        self.size = 100
        self.sizeSlider = QSlider()
        self.sizeSlider.setValue(100)
        self.sizeSlider.setMinimum(0)
        self.sizeSlider.setMaximum(200)
        self.sizeSlider.valueChanged.connect(self.updateValues)

        self.filePath = '../static/tmp_icon.png'

        self.selectFileButton = QToolButton()
        self.selectFileButton.clicked.connect(self.selectFile)
        self.selectFileButton.setText('Выбрать картинку')
        self.selectFileButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.selectFileButton.setAutoRaise(True)
        self.selectFileButton.setIconSize(QSize(64, 64))
        self.selectFileButton.setIcon(QIcon('../static/tmp_icon.png'))

        self.layout.addWidget(self.selectFileButton, 0, 0)
        self.layout.addWidget(self.toolSelector, 0, 1)
        self.layout.addWidget(self.alignmentSelector, 0, 2)
        self.layout.addWidget(WidthPictogram(), 0, 3)
        self.layout.addWidget(self.sizeSlider, 0, 4)

    # Обновление атрибутов и вызов обновления слоя-изображения (через сигнал). Сообщает сигнал signals.stateChanged
    @pyqtSlot()
    def updateValues(self) -> None:
        self.size = self.sizeSlider.value()

        self.signals.stateChanged.emit(self.size, self.alignmentSelector.state, self.toolSelector.state)

    # Вызов диалога выбора картинки с последующей ее сменой. Не делает ничего, если новая картинка не была выбрана.
    # Сообщает сигнал signals.imageChanged
    @pyqtSlot()
    def selectFile(self) -> None:
        self.filePath = QFileDialog.getOpenFileName(self, 'Выбрать картинку', '',
                                                    'Файл изображения (*.png *.jpeg *.jpg *.gif)')[0]
        if self.filePath == '':
            return

        self.signals.imageChanged.emit(self.filePath)
