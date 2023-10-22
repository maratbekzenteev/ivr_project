from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QImage, QPainter, QPalette, QBrush, QColor
from PyQt5.QtCore import Qt, QRect, QPoint


class ImageLayer(QWidget):
    def __init__(self, imagePath, width, height, parent):
        super().__init__()
        self.parent = parent

        self.image = QImage(imagePath)
        self.imagePath = imagePath

        self.setMinimumSize(width, height)
        self.setMaximumSize(width, height)
        self.resolution = width, height

        self.tool = 'none'
        self.active = False
        self.drawing = False

        self.curMousePos = QPoint(0, 0)
        self.lastMousePos = QPoint(0, 0)

        self.gridLines = []

        self.alignment = 'none'
        self.leftBorder = (1, 0)
        self.rightBorder = (1, 100)
        self.topBorder = (1, 0)
        self.bottomBorder = (1, 100)

        self.xOffset = 0
        self.yOffset = 0
        self.size = 100

        palette = self.palette()
        palette.setBrush(QPalette.Window, QBrush(QColor(0, 0, 0, alpha=0), Qt.SolidPattern))
        self.setPalette(palette)

    def setBits(self, bits):
        self.image = QImage(data=bits)

    def setImage(self, imagePath):
        self.image = QImage(imagePath)
        self.image = self.image.scaled(self.image.width() * self.size / 100, self.image.height() * self.size / 100,
                                       aspectRatioMode=Qt.IgnoreAspectRatio)

    def findBoundaryGridLines(self, x1, y1, x2, y2):
        leftGridLine = 0
        while leftGridLine < len(self.gridLines[1]) and \
                self.gridLineToOffset(1, *self.gridLines[1][leftGridLine]) <= x1:
            leftGridLine += 1
        leftGridLine -= 1

        topGridLine = 0
        while topGridLine < len(self.gridLines[0]) and \
                self.gridLineToOffset(0, *self.gridLines[0][topGridLine]) <= y1:
            topGridLine += 1
        topGridLine -= 1

        rightGridLine = len(self.gridLines[1]) - 1
        while rightGridLine > -1 and self.gridLineToOffset(1, *self.gridLines[1][rightGridLine]) >= x2:
            rightGridLine -= 1
        rightGridLine += 1

        bottomGridLine = len(self.gridLines[0]) - 1
        while bottomGridLine > -1 and self.gridLineToOffset(0, *self.gridLines[0][bottomGridLine]) >= y2:
            bottomGridLine -= 1
        bottomGridLine += 1

        return leftGridLine, rightGridLine, topGridLine, bottomGridLine

    def drawGridRect(self, painter):
        if not self.drawing or self.tool != 'grid':
            return

        qp = painter
        qp.setPen(Qt.DashLine)

        x1, y1 = self.lastMousePos.x(), self.lastMousePos.y()
        x2, y2 = self.curMousePos.x(), self.curMousePos.y()
        x1, x2 = min(x1, x2), max(x1, x2)
        y1, y2 = min(y1, y2), max(y1, y2)
        x1, y1, x2, y2 = max(x1, 1), max(y1, 1), min(x2, self.resolution[0] - 1), min(y2, self.resolution[1] - 1)
        qp.drawRect(x1, y1, x2 - x1, y2 - y1)

        leftGridLine, rightGridLine, topGridLine, bottomGridLine = self.findBoundaryGridLines(x1, y1, x2, y2)
        qp.fillRect(QRect(QPoint(self.gridLineToOffset(1, *self.gridLines[1][leftGridLine]),
                                 self.gridLineToOffset(0, *self.gridLines[0][topGridLine])),
                          QPoint(self.gridLineToOffset(1, *self.gridLines[1][rightGridLine]),
                                 self.gridLineToOffset(0, *self.gridLines[0][bottomGridLine]))),
                    QBrush(QColor(0, 0, 255, alpha=64))
                    )

    def paintEvent(self, event):
        qp = QPainter(self)
        qp.setRenderHint(QPainter.Antialiasing)

        leftBorder = self.gridLineToOffset(1, *self.leftBorder)
        rightBorder = self.gridLineToOffset(1, *self.rightBorder)
        topBorder = self.gridLineToOffset(0, *self.topBorder)
        bottomBorder = self.gridLineToOffset(0, *self.bottomBorder)

        if self.alignment == 'fill':
            qp.drawImage(QRect(QPoint(leftBorder + self.xOffset, topBorder + self.yOffset),
                               QPoint(rightBorder + self.xOffset, bottomBorder + self.yOffset)),
                         self.image)
            self.drawGridRect(qp)
            return

        if self.alignment == 'none':
            qp.drawImage(self.xOffset, self.yOffset, self.image)
            self.drawGridRect(qp)
            return

        if self.alignment in {'lt', 'left', 'lb'}:
            x = leftBorder
        elif self.alignment in {'top', 'cntr', 'bttm'}:
            x = (leftBorder + rightBorder - self.image.width()) // 2
        else:
            x = rightBorder - self.image.width()

        if self.alignment in {'lt', 'top', 'rt'}:
            y = topBorder
        elif self.alignment in {'left', 'cntr', 'rght'}:
            y = (topBorder + bottomBorder - self.image.height()) // 2
        else:
            y = bottomBorder - self.image.height()

        qp.drawImage(x + self.xOffset, y + self.yOffset, self.image)

        self.drawGridRect(qp)

    def gridLineToOffset(self, direction, indentType, indent):
        return int(self.resolution[direction ^ 1] / 100 * indent) if indentType == 1 else indent

    def updateState(self, size, alignment, tool):
        self.tool = tool
        self.alignment = alignment
        self.size = size

        self.setImage(self.imagePath)
        self.repaint()

    def updateImage(self, imagePath):
        self.setImage(imagePath)
        self.imagePath = imagePath

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

            self.repaint()
        elif not self.active and self.parent.currentLayer != -1:
            self.parent.scene.items()[self.parent.currentLayer].widget().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.active and self.drawing:
            self.drawing = False

            if self.tool == 'grid':
                x1, y1 = self.lastMousePos.x(), self.lastMousePos.y()
                x2, y2 = self.curMousePos.x(), self.curMousePos.y()
                x1, x2 = min(x1, x2), max(x1, x2)
                y1, y2 = min(y1, y2), max(y1, y2)
                x1, y1, x2, y2 = max(x1, 1), max(y1, 1), \
                                 min(x2, self.resolution[0] - 1), min(y2, self.resolution[1] - 1)

                leftGridLine, rightGridLine, topGridLine, bottomGridLine = self.findBoundaryGridLines(x1, y1, x2, y2)

                self.leftBorder = self.gridLines[1][leftGridLine]
                self.rightBorder = self.gridLines[1][rightGridLine]
                self.topBorder = self.gridLines[0][topGridLine]
                self.bottomBorder = self.gridLines[0][bottomGridLine]

                self.repaint()
        elif not self.active and self.parent.currentLayer != -1:
            self.parent.scene.items()[self.parent.currentLayer].widget().mouseMoveEvent(event)

    def setResolution(self, width, height, stretch):
        self.setMinimumSize(width, height)
        self.setMaximumSize(width, height)
        self.resolution = width, height
        self.repaint()
