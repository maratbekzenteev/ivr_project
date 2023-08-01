from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QImage, QColor, QPainter, QPen, QPalette, QBrush
from PyQt5.QtCore import Qt, QPoint
from collections import deque


class BitmapLayer(QWidget):
    def __init__(self, width, height, parent):
        super().__init__()

        self.parent = parent

        self.setMinimumSize(width, height)
        self.setMaximumSize(width, height)
        self.resolution = width, height

        self.bitmap = QImage(self.size(), QImage.Format_ARGB32_Premultiplied)
        self.bitmap.fill(QColor(0, 0, 0, alpha=0))

        self.fastBitmap = ''

        self.tool = 'none'
        self.active = False
        self.drawing = False
        self.lastMousePos = QPoint(0, 0)
        self.curMousePos = QPoint(0, 0)

        self.pen = QPen(QColor(0, 0, 0), 1, Qt.SolidLine, Qt.RoundCap, Qt.BevelJoin)

        palette = self.palette()
        palette.setBrush(QPalette.Window, QBrush(QColor(0, 0, 0, alpha=0), Qt.SolidPattern))
        self.setPalette(palette)

    def paintEvent(self, event):
        qp = QPainter(self)
        qp.drawImage(0, 0, self.bitmap)

        if self.drawing:
            if self.tool == 'rect':
                x1, y1 = self.lastMousePos.x(), self.lastMousePos.y()
                x2, y2 = self.curMousePos.x(), self.curMousePos.y()
                qp.drawRect(min(x1, x2), min(y1, y2), abs(x1 - x2), abs(y1 - y2))
            elif self.tool == 'line':
                qp.drawLine(self.lastMousePos, self.curMousePos)
            elif self.tool == 'oval':
                x1, y1 = self.lastMousePos.x(), self.lastMousePos.y()
                x2, y2 = self.curMousePos.x(), self.curMousePos.y()
                qp.drawEllipse(min(x1, x2), min(y1, y2), abs(x1 - x2), abs(y1 - y2))

    def mousePressEvent(self, event):
        if not self.active:
            self.parent.scene.items()[self.parent.currentLayer + 1].widget().mousePressEvent(event)
        else:
            if event.button() == Qt.LeftButton and self.active and self.tool != 'none':
                self.drawing = True
                self.lastMousePos = event.pos()

    def mouseMoveEvent(self, event):
        if not self.active:
            self.parent.scene.items()[self.parent.currentLayer + 1].widget().mouseMoveEvent(event)
        elif event.buttons() & Qt.LeftButton & self.drawing & self.active & (self.tool != 'none'):
            if self.tool in {'brsh', 'pen', 'penc'}:
                qp = QPainter(self.bitmap)
                qp.setPen(self.pen)
                qp.drawLine(self.lastMousePos, event.pos())

                self.lastMousePos = event.pos()
            elif self.tool != 'fill':
                self.curMousePos = event.pos()

            self.update()

    def mouseReleaseEvent(self, event):
        if self.active:
            if self.drawing:
                self.drawing = False

                if self.tool in {'rect', 'line', 'oval'}:
                    qp = QPainter(self.bitmap)
                    qp.setPen(self.pen)

                    if self.tool == 'line':
                        qp.drawLine(self.lastMousePos, self.curMousePos)
                    elif self.tool == 'rect':
                        x1, y1 = self.lastMousePos.x(), self.lastMousePos.y()
                        x2, y2 = self.curMousePos.x(), self.curMousePos.y()
                        qp.drawRect(min(x1, x2), min(y1, y2), abs(x1 - x2), abs(y1 - y2))
                    else:
                        x1, y1 = self.lastMousePos.x(), self.lastMousePos.y()
                        x2, y2 = self.curMousePos.x(), self.curMousePos.y()
                        qp.drawEllipse(min(x1, x2), min(y1, y2), abs(x1 - x2), abs(y1 - y2))
                elif self.tool == 'fill':
                    self.updateFastBitmap()
                    old_color = self.fastGetPixel(self.lastMousePos.x(), self.lastMousePos.y())
                    new_color = self.pen.color()
                    used = [[False for j in range(self.resolution[0])] for i in range(self.resolution[1])]

                    queue = deque()
                    queue.append((self.lastMousePos.x(), self.lastMousePos.y()))

                    while len(queue) != 0:
                        x, y = queue.popleft()
                        self.bitmap.setPixelColor(x, y, new_color)

                        if x != 0 and self.fastGetPixel(x - 1, y) == old_color and not used[y][x - 1]:
                            queue.append((x - 1, y))
                            used[y][x - 1] = True
                        if y != 0 and self.fastGetPixel(x, y - 1) == old_color and not used[y - 1][x]:
                            queue.append((x, y - 1))
                            used[y - 1][x] = True
                        if x != self.resolution[0] - 1 and self.fastGetPixel(x + 1, y) == old_color and not used[y][x + 1]:
                            queue.append((x + 1, y))
                            used[y][x + 1] = True
                        if y != self.resolution[1] - 1 and self.fastGetPixel(x, y + 1) == old_color and not used[y + 1][x]:
                            queue.append((x, y + 1))
                            used[y + 1][x] = True

                self.lastMousePos = QPoint(0, 0)
                self.curMousePos = QPoint(0, 0)

                self.update()
        else:
            self.parent.scene.items()[self.parent.currentLayer + 1].widget().mouseReleaseEvent(event)

    def updateState(self, color, width, tool):
        self.pen.setColor(color)
        self.pen.setWidth(width)
        self.tool = tool

        if self.tool == 'penc':
            self.pen.setCapStyle(Qt.FlatCap)
        elif self.tool == 'pen':
            self.pen.setCapStyle(Qt.SquareCap)
        else:
            self.pen.setCapStyle(Qt.RoundCap)

    def updateFastBitmap(self):
        self.fastBitmap = self.bitmap.bits().asstring(self.resolution[0] * self.resolution[1] * 4)

    def fastGetPixel(self, x, y):
        i = (x + (y * self.resolution[0])) * 4
        return self.fastBitmap[i:i + 4]
