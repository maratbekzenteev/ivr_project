from PyQt5.QtWidgets import QWidget, QSpinBox, QFontComboBox, QToolButton, QGridLayout
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtCore import pyqtSlot, Qt
from colorPreview import ColorPreview
from toolSelector import ToolSelector
from signals import Signals


class TextToolbar(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QGridLayout(self)
        self.setLayout(self.layout)

        self.signals = Signals()

        self.color = QColor(0, 0, 0)
        self.colorPreview = ColorPreview()
        self.colorPreview.signals.valueChanged.connect(self.updateValues)

        self.font = 'Verdana'
        self.fontComboBox = QFontComboBox()
        self.fontComboBox.setFont(QFont('Verdana'))
        self.fontComboBox.currentFontChanged.connect(self.updateValues)

        self.sizeSpinBox = QSpinBox()
        self.sizeSpinBox.setMinimum(1)
        self.sizeSpinBox.setMaximum(256)
        self.sizeSpinBox.setValue(32)
        self.size = 32
        self.sizeSpinBox.valueChanged.connect(self.updateValues)

        self.fontWeight = QFont.Normal
        self.fontWeightButton = QToolButton()
        self.fontWeightButton.setText('Ж')
        self.fontWeightButton.setAutoRaise(True)
        self.fontWeightButton.setCheckable(True)
        self.fontWeightButton.clicked.connect(self.updateValues)

        self.italic = False
        self.italicButton = QToolButton()
        self.italicButton.setText('К')
        self.italicButton.setAutoRaise(True)
        self.italicButton.setCheckable(True)
        self.italicButton.clicked.connect(self.updateValues)

        self.underline = False
        self.underlineButton = QToolButton()
        self.underlineButton.setText('П')
        self.underlineButton.setAutoRaise(True)
        self.underlineButton.setCheckable(True)
        self.underlineButton.clicked.connect(self.updateValues)

        self.alignment = Qt.AlignLeft
        self.stringToQtAlignment = {
            'none': Qt.AlignLeft,
            'left': Qt.AlignLeft,
            'cntr': Qt.AlignCenter,
            'rght': Qt.AlignRight,
            'fill': Qt.AlignJustify
        }
        self.alignmentSelector = ToolSelector('Слева', 'По центру', 'Справа', 'Заполнить')
        self.alignmentSelector.setStates('left', 'cntr', 'rght', 'fill')
        self.alignmentSelector.signals.valueChanged.connect(self.updateValues)

        self.layout.addWidget(self.fontComboBox, 0, 0)
        self.layout.addWidget(self.sizeSpinBox, 0, 1)
        self.layout.addWidget(self.fontWeightButton, 0, 2)
        self.layout.addWidget(self.italicButton, 0, 3)
        self.layout.addWidget(self.underlineButton, 0, 4)
        self.layout.addWidget(self.colorPreview, 0, 5)
        self.layout.addWidget(self.alignmentSelector, 0, 6)

    @pyqtSlot()
    def updateValues(self):
        self.color = self.colorPreview.color
        self.font = self.fontComboBox.currentFont()
        self.size = self.sizeSpinBox.value()
        self.fontWeight = QFont.Weight.DemiBold if self.fontWeightButton.isChecked() else QFont.Weight.Normal
        self.italic = self.italicButton.isChecked()
        self.underline = self.underlineButton.isChecked()
        self.alignment = self.stringToQtAlignment[self.alignmentSelector.state]

        self.signals.valueChanged.emit()

    def setState(self, color, font, size, fontWeight, italic, underline, alignment):
        self.color = color
        self.colorPreview.setColor(color)
        self.font = font
        self.fontComboBox.setFont(QFont(font))
        self.fontWeight = fontWeight
        self.fontWeightButton.setChecked(fontWeight == QFont.Weight.DemiBold)
        self.italic = italic
        self.italicButton.setChecked(italic)
        self.underline = underline
        self.underlineButton.setChecked(underline)
        self.size = size
        self.alignment = alignment
        for i in self.stringToQtAlignment:
            if self.stringToQtAlignment[i] == alignment:
                self.alignmentSelector.setState(i)
                break
