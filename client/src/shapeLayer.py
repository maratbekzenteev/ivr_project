from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPalette, QBrush, QColor, QPaintEvent, QMouseEvent
from PyQt5.QtCore import Qt, QRect, QPoint


# Класс фигурного слоя. Сигналов не сообщает
# Атрибуты:
# - self.parent - QWidget, родительский виджет главного окна, через который слой получает информацию о сетке
# - self.resolution - tuple(int, int), кортеж из ширины и высоты слоя, а равно и всего проекта
# - self.tool - str, текущий метод работы со слоем. Значения:
# - - 'none' - никакой инструмент не выбран
# - - 'grid' - выбирается прямоугольник из линий сетки, которым фигура определяется
# - - 'ofst' - задается отступ - "оффсет" - в пикселях от точки, где фигура должна лежать идеально по сетке
# - self.shape - str, тип фигуры. Значения:
# - - 'none' - фигура не выбрана
# - - 'line' - отрезок от пересечения self.firstVBorder и self.firstHBorder до пересечения
# - - - self.secondVBorder и self.secondHBorder
# - - 'rect' - прямоугольник, ограниченный self.firstVBorder, self.firstHBorder, self.secondVBorder, self.secondHBorder
# - - 'oval' - овал, ограниченный self.firstVBorder, self.firstHBorder, self.secondVBorder, self.secondHBorder
# - self.lineColor - QColor, цвет обводки фигуры
# - self.fillColor - QColor, цвет заливки фигуры
# - self.width - int, толщина обводки. Принимает значения от 0 до 32
# - self.active - bool, True - слой активирован (доступен для изменения), False - слой деактивирован
# - self.drawing - bool, True - ЛКМ нажата, пользователь "рисует" (выбирает ограничивающие линии,
# - - которыми картинка задаётся), False - ЛКМ отпущена.
# - self.curMousePos - QPoint, точка, задающая первую пару ограничительных линий
# - self.lastMousePos - QPoint, точка, задающая вторую пару ограничительных линий
# - self.gridLines - list(list(tuple(int, int))) - список линий сетки. Под индеком 0 - горизонтальные, 1 - вертикальные.
# - - В каждом подсписке линия сетки задаётся как tuple(indentType, indent), где indentType - тип отступа линии
# - - от верхнего (для горизонтальных) или левого (для вертикальных) края, значения:
# - - - 0 - абсолютный отступ (задаётся в пикселях переменной indent)
# - - - 1 - относительный отступ (задаётся в процентах от высоты (для горизонтальных) или ширины (для вертикальных)
# - - - - изображения переменной indent)
# - self.firstVBorder - tuple(int, int), первая вертикальная ограничительная линия сетки
# - self.firstHBorder - tuple(int, int), первая горизонтальная ограничительная линия сетки
# - self.secondVBorder - tuple(int, int), вторая вертикальная ограничительная линия сетки
# - self.secondHBorder - tuple(int, int), вторая горизонтальная ограничительная линия сетки
# - self.xOffset - int, отступ по горизонтали в пикселях от точки, где фигура должна лежать идеально по сетке
# - self.yOffset - int, отступ по вертикали в пикселях от точки, где фигура должна лежать идеально по сетке
class ShapeLayer(QWidget):
    def __init__(self, width: int, height: int, parent: QWidget) -> None:
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

    # Функция нахождения ближайших вертикальной и горизонтальной линий сетки к точке. Используется при задании
    # пользователем ограничительных линий фигуры
    def findNearestGridlines(self, point: QPoint) -> tuple[tuple[int, int], tuple[int, int]]:
        x, y = point.x(), point.y()
        hLine = min(self.gridLines[0], key=lambda i: abs(y - self.gridLineToOffset(0, *i)))
        vLine = min(self.gridLines[1], key=lambda i: abs(x - self.gridLineToOffset(1, *i)))

        return hLine, vLine

    # Отрисовка содержимого слоя. Если пользователь "рисует" на слое, помимо самой фигуры отрисовываются также
    # вспомогательные элементы, помогающие пользователю понять, куда "прикрепилась" фигура, а также "тень" фигуры,
    # рисующаяся не по ближайшим линиям сетки, а точно по нажатиям пользователя
    def paintEvent(self, event: QPaintEvent) -> None:
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
            qp.drawLine(QPoint(x1, y1) + QPoint(self.xOffset, self.yOffset),
                        QPoint(x2, y2) + QPoint(self.xOffset, self.yOffset))
        elif self.shape == 'rect':
            qp.drawRect(min(x1, x2) + self.xOffset, min(y1, y2) + self.yOffset, abs(x1 - x2), abs(y1 - y2))
        elif self.shape == 'oval':
            qp.drawEllipse(min(x1, x2) + self.xOffset, min(y1, y2) + self.yOffset, abs(x1 - x2), abs(y1 - y2))

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

    # Функция преобразования линии сетки в отступ от левого верхнего края (в пикселях), используется при нахождении
    # ограничивающих линий сетки и отрисовке слоя. Подробнее о формате аргументов см. в комментарии
    # к самому классу
    def gridLineToOffset(self, direction: int, indentType: int, indent: int) -> int:
        return int(self.resolution[direction ^ 1] / 100 * indent) if indentType == 1 else indent

    def updateState(self, lineColor, fillColor, width, tool, shape):
        self.lineColor = lineColor
        self.fillColor = fillColor
        self.width = width
        self.tool = tool
        self.shape = shape

        self.repaint()

    # Обработчик нажатия кнопки мыши. Если слой неактивен, но находится поверх остальных (имеет наибольший z),
    # то event будет приходить ему. В таком случае слой через self.parent передает нажатие на нужный слой.
    # В противном случае включается self.drawing и обновляется self.lastMousePos (при задании и оффсета, и
    # ограничивающих прямых он используется)
    def mousePressEvent(self, event: QMouseEvent) -> None:
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

    # Обработчик движения мыши. Если слой неактивен, но находится поверх остальных (имеет наибольший z),
    # то event будет приходить ему. В таком случае слой через self.parent передает нажатие на нужный слой.
    # В противном случае проверяется, что мышь уже была нажата ранее и выбран инструмент.
    # Если инструмент - задание оффсета, то оффсет сразу обновляется для корректной перерисовки слоя, если
    # задаётся прямоугольник линий сетки, то меняется лишь его вторая задающая точка
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
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

    # Обработчик отпускания кнопки мыши. Если слой неактивен, но находится поверх остальных (имеет наибольший z),
    # то event будет приходить ему. В таком случае слой через self.parent передает нажатие на нужный слой.
    # В противном случае проверяется, идет ли сейчас рисование. Если да, то оно заканчивается
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self.active and self.drawing:
            self.drawing = False
            self.repaint()
        elif not self.active and self.parent.currentLayer != -1:
            self.parent.scene.items()[self.parent.currentLayer].widget().mouseMoveEvent(event)

    # Задание нового разрешения. Вызывается родительским классом Window при изменении разрешения проекта
    # параметр stretch ничего не задаёт, так как фигура в любом случае должна подгоняться под обновлённую сетку
    def setResolution(self, width: int, height: int, stretch: bool) -> None:
        self.setMinimumSize(width, height)
        self.setMaximumSize(width, height)
        self.resolution = width, height
        self.repaint()
