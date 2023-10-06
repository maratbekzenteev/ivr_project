from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QImage, QColor, QPainter, QPen, QPalette, QBrush
from PyQt5.QtCore import Qt, QPoint
from collections import deque


# В этом файле описан класс растрового слоя, помещаемый на сцену Window.scene при помощи QProxyWidget

# Класс растрового слоя. Сигналов не сообщает.
# Аттрибуты:
# - self.parent - QWidget, ссылка на родительский виджет (Window).
# - - Используется для передачи нажатий на активный слой, т.к. напрямую это делать затратно
# - self.resolution - (int, int), разрешение слоя, а равно и всего проекта
# - self.bitmap - QImage, содержимое слоя. Используется для рисования на слое инструментами QPainter
# - self.fastBitmap - str, содержимое слоя. Используется для быстрого прямого доступа к точкам (инструментом заливки).
# - - Обновляется по требованию, т.е. в начале процедуры заливки
# - self.tool - str (в будущем планируется заменить на Enum), текущий выбранный инструмент
# - - Значения (названия имеют длину до 4 симв. включительно, чтобы ускорить сравнение строк):
# - - - 'none' - инструмент не выбран
# - - - 'brsh' - кисть. След кисти идёт по траектории движения мыши с опущенной ЛКМ. Форма следа округлая (Qt.RoundCap)
# - - - 'pen' - ручка. То же, что и кисть, но с более угловатой формой следа (Qt.SquareCap)
# - - - 'penc' - карандаш. То же, что и кисть, но с более отрывистой формой следа (Qt.FlatCap)
# - - - 'line' - отрезок. Соединяет отрезком точку нажания и точку отпускания ЛКМ.
# - - - 'rect' - прямоугольник. Строит прямоугольник по диагонали, заданной пользователем как отрезок, соединяющий
# - - - - точку нажатия и точку отпускания ЛКМ, со сторонами, параллельными осям координат
# - - - 'oval' - эллипс. Строит эллипс, вписанный в прямоугольник, построенный описанным выше способом
# - - - 'fill' - заливка. Меняет цвет области точек цвета точки, в которой была нажата ЛКМ. Область ограничена
# - - - - точками другого цвета
# - self.active - bool, True - слой активирован (доступен для изменения), False - слой деактивирован
# - self.drawing - bool, True - ЛКМ нажата, пользователь рисует, False - ЛКМ отпущена.
# - - Необходим для предотвращения рисования при перемещении мыши, когда пользователь не начал рисовать.
# - self.lastMousePos - QPoint, координаты предыдущей точки рисуемой точки кривой (для кисти, ручки, карандаша) или
# - -  координаты первой точки, от которой рисуется фигура (для отрезка, прямоугольника, эллипса)
# - self.curMousePos - QPoint, используется при рисовании отрезка, прямоугольника, эллипса. Вторая точка, по которой
# - - рисуется фигура
# - self.pen - QPen, задает стиль рисования ("начертание пера"), цвет и толщину
class BitmapLayer(QWidget):
    # Инициализация аттрибутов, изменение фона на прозрачный
    def __init__(self, width: int, height: int, parent: QWidget):
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

    # Отрисовка виджета слоя. Помимо самого содержимого слоя, если пользователь не закончил рисовать
    # отрезок, прямоугольник или эллипс, поверх слоя тонкой линией также будет отрисована рисуемая фигура
    def paintEvent(self, event):
        qp = QPainter(self)
        qp.drawImage(0, 0, self.bitmap)

        if self.drawing:
            qp.setPen(Qt.DashLine)

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
            elif self.tool == 'ersr':
                qp.drawEllipse(self.lastMousePos.x() - self.pen.width() // 2,
                               self.lastMousePos.y() - self.pen.width() // 2,
                               self.pen.width(), self.pen.width())

    # Обработчик нажатия мыши. Если слой неактивен, но находится поверх остальных (имеет наибольший z),
    # то event будет приходить ему. В таком случае слой через self.parent передает нажатие на нужный слой.
    # В противном случае включается self.drawing и обновляется self.lastMousePos
    def mousePressEvent(self, event):
        if not self.active:
            if self.parent.currentLayer != -1:
                self.parent.scene.items()[self.parent.currentLayer].widget().mousePressEvent(event)
        else:
            if event.button() == Qt.LeftButton and self.active and self.tool != 'none':
                self.drawing = True
                self.lastMousePos = event.pos()

    # Обработчик движения мыши. Если слой неактивен, но находится поверх остальных (имеет наибольший z),
    # то event будет приходить ему. В таком случае слой через self.parent передает нажатие на нужный слой.
    # В противном случае проверяется, что мышь уже была нажата ранее и выбран инструмент.
    # Если инструмент - кисть, ручка или карандаш, то результат рисования наносится на self.bitmap сразу.
    # Если это отрезок, прямоугольник или эллипс, то обновляется только self.curMousePos для корректной отрисовки
    # предпросмотра рисуемой фигуры
    def mouseMoveEvent(self, event):
        if not self.active:
            if self.parent.currentLayer != -1:
                self.parent.scene.items()[self.parent.currentLayer].widget().mouseMoveEvent(event)
        elif event.buttons() & Qt.LeftButton & self.drawing & (self.tool != 'none'):
            if self.tool in {'brsh', 'pen', 'penc', 'ersr'}:
                qp = QPainter(self.bitmap)
                qp.setPen(self.pen)
                if self.tool == 'ersr':
                    qp.setCompositionMode(QPainter.CompositionMode_Clear)
                qp.drawLine(self.lastMousePos, event.pos())

                self.lastMousePos = event.pos()
            elif self.tool != 'fill':
                self.curMousePos = event.pos()

            self.update()

    # Обработчик отпускания кнопок мыши. Если слой неактивен, но находится поверх остальных (имеет наибольший z),
    # то event будет приходить ему. В таком случае слой через self.parent передает нажатие на нужный слой.
    # В противном случае проверяется, идет ли сейчас рисование. Если да, то оно заканчивается, => надо нарисовать
    # отрезок, прямоугольник или эллипс. Если инструмент - заливка, то обходом в ширину закрашиваются точки того же
    # цвета, что и точка заливки, находящиеся в одной области с ней. Для ускорения процесса используется быстрый доступ
    # к точкам слоя при помощи предварительно обновленного self.fastBitmap. Заливка работает медленно
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
        elif self.parent.currentLayer != -1:
            self.parent.scene.items()[self.parent.currentLayer].widget().mouseReleaseEvent(event)

    # Обновление инструмента, цвета и толщины рисования на слое
    def updateState(self, color: QColor, width: int, tool: str) -> None:
        self.pen.setColor(color)
        self.pen.setWidth(width)
        self.tool = tool

        if self.tool == 'penc':
            self.pen.setCapStyle(Qt.FlatCap)
        elif self.tool == 'pen':
            self.pen.setCapStyle(Qt.SquareCap)
        else:
            self.pen.setCapStyle(Qt.RoundCap)

    # Обновление self.fastBitmap
    def updateFastBitmap(self):
        self.fastBitmap = self.bitmap.bits().asstring(self.resolution[0] * self.resolution[1] * 4)

    # Быстрый доступ к пикселю при помощи self.fastBitmap
    def fastGetPixel(self, x: int, y: int) -> str:
        i = (x + (y * self.resolution[0])) * 4
        return self.fastBitmap[i:i + 4]
