from PyQt5.QtWidgets import QWidget, QTextEdit, QFrame
from PyQt5.QtGui import QColor, QPalette, QBrush, QPainter, QFont
from PyQt5.QtCore import QPoint, Qt, QRect, pyqtSlot

class TextLayer(QWidget):
    def __init__(self, width, height, parent):
        super().__init__()
        self.parent = parent

        self.setMinimumSize(width, height)
        self.setMaximumSize(width, height)
        self.resolution = width, height

        self.textEdit = QTextEdit(self)
        self.textEdit.setGeometry(0, 0, 0, 0)
        self.textEdit.setFrameShape(QFrame.NoFrame)
        self.textEdit.setStyleSheet("background: rgba(0,0,0,0%)")

        self.color = QColor(0, 0, 0)
        self.font = "Verdana"
        self.size = 32
        self.fontWeight = QFont.Weight.Normal
        self.italic = False
        self.underline = False
        self.alignment = Qt.AlignLeft
        self.textEdit.setFont(QFont("Verdana", 32))
        self.textEdit.setFontPointSize(32)
        self.textEdit.cursorPositionChanged.connect(self.updateFromNewCursorPosition)

        self.active = False
        self.drawing = False
        self.previousZValue = -1

        self.curMousePos = QPoint(0, 0)
        self.lastMousePos = QPoint(0, 0)

        self.gridLines = []

        self.leftBorder = (1, 0)
        self.rightBorder = (1, 100)
        self.topBorder = (1, 0)
        self.bottomBorder = (1, 100)

        palette = self.palette()
        palette.setBrush(QPalette.Window, QBrush(QColor(0, 0, 0, alpha=0), Qt.SolidPattern))
        self.setPalette(palette)

    def gridLineToOffset(self, direction, indentType, indent):
        return int(self.resolution[direction ^ 1] / 100 * indent) if indentType == 1 else indent

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
        if not self.drawing:
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
        if self.active:
            x1 = self.gridLineToOffset(1, *self.leftBorder)
            x2 = self.gridLineToOffset(1, *self.rightBorder)
            y1 = self.gridLineToOffset(0, *self.topBorder)
            y2 = self.gridLineToOffset(0, *self.bottomBorder)
            qp.setPen(Qt.DashLine)
            qp.drawRect(QRect(QPoint(x1, y1), QPoint(x2, y2)))

        self.drawGridRect(qp)

    def mousePressEvent(self, event):
        if self.active:
            print(self.textEdit.geometry())
            print([i.widget().testAttribute(Qt.WA_TransparentForMouseEvents) for i in self.parent.scene.items()])

            self.drawing = True
            self.lastMousePos = event.pos()
            self.curMousePos = event.pos()

            self.gridLines = [self.parent.scene.items()[1].widget().hLines,
                              self.parent.scene.items()[1].widget().vLines]
        elif self.parent.currentLayer != -1:
            self.parent.scene.items()[self.parent.currentLayer].widget().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.active and self.drawing:
            self.curMousePos = event.pos()

            self.repaint()
        elif not self.active and self.parent.currentLayer != -1:
            self.parent.scene.items()[self.parent.currentLayer].widget().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.active and self.drawing:
            self.drawing = False

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

            x1 = self.gridLineToOffset(1, *self.leftBorder)
            x2 = self.gridLineToOffset(1, *self.rightBorder)
            y1 = self.gridLineToOffset(0, *self.topBorder)
            y2 = self.gridLineToOffset(0, *self.bottomBorder)
            self.textEdit.setGeometry(x1, y1, x2 - x1, y2 - y1)
            self.textEdit.show()
            self.repaint()
        elif not self.active and self.parent.currentLayer != -1:
            self.parent.scene.items()[self.parent.currentLayer].widget().mouseMoveEvent(event)

    def storeZValue(self, z):
        self.previousZValue = z

    def updateState(self, color, font, size, fontWeight, italic, underline, alignment):
        self.color = color
        self.textEdit.setTextColor(color)
        self.font = font
        self.textEdit.setFont(QFont(font))
        self.size = size
        self.textEdit.setFontPointSize(size)
        self.fontWeight = fontWeight
        self.textEdit.setFontWeight(fontWeight)
        self.italic = italic
        self.textEdit.setFontItalic(italic)
        self.underline = underline
        self.textEdit.setFontUnderline(underline)
        self.alignment = alignment
        self.textEdit.setAlignment(alignment)

    def updateFromNewCursorPosition(self):
        self.color = self.textEdit.textColor()
        self.font = self.textEdit.font().key()
        self.size = self.textEdit.fontPointSize()
        self.fontWeight = self.textEdit.fontWeight()
        self.italic = self.textEdit.fontItalic()
        self.underline = self.textEdit.fontUnderline()
        self.alignment = self.textEdit.alignment()

        self.parent.updateTextToolbarState()
