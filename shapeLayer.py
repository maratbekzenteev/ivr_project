from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPalette, QBrush, QColor, QPen
from PyQt5.QtCore import Qt, QRect, QPoint


class ShapeLayer(QWidget):
    def __init__(self, width, height, parent):
        super().__init__()
        self.parent = parent

        self.setMinimumSize(width, height)
        self.setMaximumSize(width, height)
        self.resolution = width, height

        self.tool = 'none'
        self.shape = 'none'
        self.lineColor = QColor(0, 0, 0)
        self.fillColor = QColor(0, 0, 0)
        self.width = 0

        self.active = False
        self.drawing = False

        self.curMousePos = QPoint(0, 0)
        self.lastMousePos = QPoint(0, 0)

        self.gridLines = []

        self.firstVBorder = (1, 0)
        self.secondVBorder = (1, 100)
        self.firstHBorder = (1, 0)
        self.secondHBorder = (1, 100)

        self.xOffset = 0
        self.yOffset = 0

        palette = self.palette()
        palette.setBrush(QPalette.Window, QBrush(QColor(0, 0, 0, alpha=0), Qt.SolidPattern))
        self.setPalette(palette)

    def setResolution(self, width, height):
        self.resolution = width, height
        self.repaint()

    def findNearestGridlines(self, point: QPoint) -> tuple[tuple, tuple]:
        x, y = point.x(), point.y()
        hLine = min(self.gridLines[0], key=lambda i: abs(y - self.gridLineToOffset(0, *i)))
        vLine = min(self.gridLines[1], key=lambda i: abs(x - self.gridLineToOffset(1, *i)))

        return hLine, vLine

    def paintEvent(self, event):
        qp = QPainter(self)
        pen = qp.pen()
        pen.setWidth(self.width)
        pen.setColor(self.lineColor)
        qp.setPen(pen)
        qp.setBrush(self.fillColor)

        x1 = self.gridLineToOffset(1, *self.firstVBorder)
        x2 = self.gridLineToOffset(1, *self.secondVBorder)
        y1 = self.gridLineToOffset(0, *self.firstHBorder)
        y2 = self.gridLineToOffset(0, *self.secondHBorder)

        if self.shape == 'none':
            return
        if self.shape == 'line':
            qp.drawLine(QPoint(x1, y1), QPoint(x2, y2))
        elif self.shape == 'rect':
            qp.drawRect(min(x1, x2), min(y1, y2), abs(x1 - x2), abs(y1 - y2))
        elif self.shape == 'oval':
            qp.drawEllipse(min(x1, x2), min(y1, y2), abs(x1 - x2), abs(y1 - y2))

        if self.drawing and self.shape != 'none' and self.tool == 'grid':
            qp = QPainter(self)
            qp.setPen(Qt.DashLine)
            qp.setBrush(qp.background())

            if self.shape == 'line':
                qp.drawLine(self.lastMousePos, self.curMousePos)
            else:
                qp.drawRect(min(self.lastMousePos.x(), self.curMousePos.x()),
                            min(self.lastMousePos.y(), self.curMousePos.y()),
                            abs(self.lastMousePos.x() - self.curMousePos.x()),
                            abs(self.lastMousePos.y() - self.curMousePos.y()))

            qp.fillRect(QRect(QPoint(x1, y1) - QPoint(16, 16), QPoint(x1, y1) + QPoint(16, 16)),
                        QBrush(QColor(0, 0, 255, alpha=64)))
            qp.fillRect(QRect(QPoint(x2, y2) - QPoint(16, 16), QPoint(x2, y2) + QPoint(16, 16)),
                        QBrush(QColor(0, 0, 255, alpha=64)))

    def gridLineToOffset(self, direction, indentType, indent):
        return int(self.resolution[direction ^ 1] / 100 * indent) if indentType == 1 else indent

    def updateState(self, lineColor, fillColor, width, tool, shape):
        self.lineColor = lineColor
        self.fillColor = fillColor
        self.width = width
        self.tool = tool
        self.shape = shape

        self.repaint()

    def mousePressEvent(self, event):
        if self.active:
            if self.tool == 'none':
                return

            self.drawing = True
            self.lastMousePos = event.pos()
            self.curMousePos = event.pos()

            if self.tool == 'grid':
                self.gridLines = [self.parent.scene.items()[1].widget().hLines,
                                  self.parent.scene.items()[1].widget().vLines]

                self.firstHBorder, self.firstVBorder = self.findNearestGridlines(self.lastMousePos)
        elif self.parent.currentLayer != -1:
            self.parent.scene.items()[self.parent.currentLayer].widget().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.active and self.drawing:
            if self.tool == 'ofst':
                self.xOffset += event.pos().x() - self.lastMousePos.x()
                self.yOffset += event.pos().y() - self.lastMousePos.y()
                self.lastMousePos = event.pos()
            elif self.tool == 'grid':
                self.curMousePos = event.pos()
                self.secondHBorder, self.secondVBorder = self.findNearestGridlines(self.curMousePos)

            self.repaint()
        elif not self.active and self.parent.currentLayer != -1:
            self.parent.scene.items()[self.parent.currentLayer].widget().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.active and self.drawing:
            self.drawing = False
            self.repaint()
        elif not self.active and self.parent.currentLayer != -1:
            self.parent.scene.items()[self.parent.currentLayer].widget().mouseMoveEvent(event)
