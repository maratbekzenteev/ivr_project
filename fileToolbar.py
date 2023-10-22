from PyQt5.QtWidgets import QWidget, QGridLayout, QToolButton
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize, Qt


class FileToolbar(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QGridLayout(self)
        self.setLayout(self.layout)

        self.newButton = QToolButton()
        self.newButton.setText('Новый проект')
        self.newButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.newButton.setAutoRaise(True)
        self.newButton.setIconSize(QSize(64, 64))
        self.newButton.setIcon(QIcon('tmp_icon.png'))

        self.exportButton = QToolButton()
        self.exportButton.setText('Экспортировать в изображение')
        self.exportButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.exportButton.setAutoRaise(True)
        self.exportButton.setIconSize(QSize(64, 64))
        self.exportButton.setIcon(QIcon('tmp_icon.png'))

        self.saveButton = QToolButton()
        self.saveButton.setText('Сохранить на компьютер')
        self.saveButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.saveButton.setAutoRaise(True)
        self.saveButton.setIconSize(QSize(64, 64))
        self.saveButton.setIcon(QIcon('tmp_icon.png'))

        self.cloudSaveButton = QToolButton()
        self.cloudSaveButton.setText('Сохранить в облако')
        self.cloudSaveButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.cloudSaveButton.setAutoRaise(True)
        self.cloudSaveButton.setIconSize(QSize(64, 64))
        self.cloudSaveButton.setIcon(QIcon('tmp_icon.png'))

        self.openButton = QToolButton()
        self.openButton.setText('Открыть с компьютера')
        self.openButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.openButton.setAutoRaise(True)
        self.openButton.setIconSize(QSize(64, 64))
        self.openButton.setIcon(QIcon('tmp_icon.png'))

        self.cloudOpenButton = QToolButton()
        self.cloudOpenButton.setText('Открыть из облака')
        self.cloudOpenButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.cloudOpenButton.setAutoRaise(True)
        self.cloudOpenButton.setIconSize(QSize(64, 64))
        self.cloudOpenButton.setIcon(QIcon('tmp_icon.png'))

        self.undoButton = QToolButton()
        self.undoButton.setText('Убрать последнюю линию')
        self.undoButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.undoButton.setAutoRaise(True)
        self.undoButton.setIconSize(QSize(64, 64))
        self.undoButton.setIcon(QIcon('tmp_icon.png'))

        self.redoButton = QToolButton()
        self.redoButton.setText('Вернуть убранную линию')
        self.redoButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.redoButton.setAutoRaise(True)
        self.redoButton.setIconSize(QSize(64, 64))
        self.redoButton.setIcon(QIcon('tmp_icon.png'))

        self.resizeButton = QToolButton()
        self.resizeButton.setText('Изменить разрешение')
        self.resizeButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.resizeButton.setAutoRaise(True)
        self.resizeButton.setIconSize(QSize(64, 64))
        self.resizeButton.setIcon(QIcon('tmp_icon.png'))

        self.layout.addWidget(self.newButton, 0, 0, alignment=Qt.AlignLeft)
        self.layout.addWidget(self.exportButton, 1, 0, alignment=Qt.AlignLeft)
        self.layout.addWidget(self.openButton, 0, 1, alignment=Qt.AlignLeft)
        self.layout.addWidget(self.cloudOpenButton, 1, 1, alignment=Qt.AlignLeft)
        self.layout.addWidget(self.saveButton, 0, 2, alignment=Qt.AlignLeft)
        self.layout.addWidget(self.cloudSaveButton, 1, 2, alignment=Qt.AlignLeft)
        self.layout.addWidget(self.undoButton, 0, 3, alignment=Qt.AlignLeft)
        self.layout.addWidget(self.redoButton, 1, 3, alignment=Qt.AlignLeft)
        self.layout.addWidget(self.resizeButton, 0, 4, alignment=Qt.AlignLeft)
