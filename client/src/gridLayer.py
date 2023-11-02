from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QColor, QPainter, QPalette, QBrush
from PyQt5.QtCore import Qt


class GridLayer(QWidget):
    def __init__(self, width, height):
        super().__init__()

        self.setMinimumSize(width, height)
        self.setMaximumSize(width, height)
        self.width = width
        self.height = height

        self.active = False

        self.hLines = [(1, 0), (1, 100)]
        self.vLines = [(1, 0), (1, 100)]

        palette = self.palette()
        palette.setBrush(QPalette.Window, QBrush(QColor(0, 0, 0, alpha=0), Qt.SolidPattern))
        self.setPalette(palette)

    # indentType == 0: absolute, indentType == 1: relative
    def addLine(self, direction: int, indentType: int, indent: int):
        if direction == 0:
            self.hLines.append((indentType, indent))
        elif direction == 1:
            self.vLines.append((indentType, indent))

        self.sort()
        self.repaint()

    def deleteLine(self, direction: int, indentType: int, indent: int):
        if direction == 0:
            self.hLines.remove((indentType, indent))
        elif direction == 1:
            self.vLines.remove((indentType, indent))

        self.repaint()

    def sort(self):
        self.hLines.sort(key=lambda x: x[1] if x[0] == 0 else self.height / 100 * x[1])
        self.vLines.sort(key=lambda x: x[1] if x[0] == 0 else self.width / 100 * x[1])

    def paintEvent(self, event):
        qp = QPainter(self)
        pen = qp.pen()
        pen.setWidth(4)
        pen.setColor(QColor(0, 0, 255))
        qp.setPen(pen)

        for indentType, indent in self.hLines:
            if indentType == 0:
                qp.drawLine(0, indent, self.width, indent)
            elif indentType == 1:
                qp.drawLine(0, int(self.height / 100 * indent), self.width, int(self.height / 100 * indent))
        for indentType, indent in self.vLines:
            if indentType == 0:
                qp.drawLine(indent, 0, indent, self.height)
            elif indentType == 1:
                qp.drawLine(int(self.width / 100 * indent), 0, int(self.width / 100 * indent), self.height)

    def setResolution(self, width, height, stretch):
        self.width, self.height = width, height
        self.repaint()
