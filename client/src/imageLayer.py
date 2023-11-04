from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QImage, QPainter, QPalette, QBrush, QColor, QPaintEvent, QMouseEvent
from PyQt5.QtCore import Qt, QRect, QPoint


# Класс слоя-картинки. Сигналов не сообщает
# Атрибуты:
# - self.parent - QWidget, родительский виджет главного окна, через который слой получает информацию о сетке
# - self.resolution - tuple(int, int), кортеж из ширины и высоты слоя, а равно и всего проекта
# - self.image - QImage, картинка, рисующаяся на слое
# - self.imagePath - str, путь до картинки, которая отображается на слое (если файл проекта не создан с нуля,
# - - а открыт из gri-файла, то данные о картинке будут загружены оттуда)
# - self.tool - str, текущий метод работы со слоем. Значения:
# - - 'none' - никакой инструмент не выбран
# - - 'grid' - выбирается прямоугольник из линий сетки, в котором картинка лежит
# - - 'ofst' - задается отступ - "оффсет" - в пикселях от точки, где картинка должна лежать идеально по сетке
# - self.active - bool, True - слой активирован (доступен для изменения), False - слой деактивирован
# - self.drawing - bool, True - ЛКМ нажата, пользователь "рисует" (выбирает прямоугольник,
# - - в котором картинка лежит), False - ЛКМ отпущена.
# - self.curMousePos - QPoint, первая точка, задающая прямоугольник, в котором будет лежать картинка, "рисуемый" сейчас
# - self.lastMousePos - QPoint, вторяя точка, задающая прямоугольник, в котором будет лежать картинка, "рисуемый" сейчас
# - self.gridLines - list(list(tuple(int, int))) - список линий сетки. Под индеком 0 - горизонтальные, 1 - вертикальные.
# - - В каждом подсписке линия сетки задаётся как tuple(indentType, indent), где indentType - тип отступа линии
# - - от верхнего (для горизонтальных) или левого (для вертикальных) края, значения:
# - - - 0 - абсолютный отступ (задаётся в пикселях переменной indent)
# - - - 1 - относительный отступ (задаётся в процентах от высоты (для горизонтальных) или ширины (для вертикальных)
# - - - - изображения переменной indent)
# - self.alignment - str, выравниваение текущего слоя-картинки относительно сетки. Значения:
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
# - self.leftBorder - tuple(indentType, indent), левая сторона прямоугольника, задаётся описанным выше образом
# - self.rightBorder - tuple(indentType, indent), правая сторона прямоугольника, задаётся описанным выше образом
# - self.topBorder - tuple(indentType, indent), верхняя сторона прямоугольника, задаётся описанным выше образом
# - self.bottomBorder - tuple(indentType, indent), нижняя сторона прямоугольника, задаётся описанным выше образом
# - self.xOffset - int, отступ по горизонтали в пикселях от точки, где картинка должна лежать идеально по сетке
# - self.yOffset - int, отступ по вертикали в пикселях от точки, где картинка должна лежать идеально по сетке
# - self.size - int, масштаб, в котором картинка отображается (в процентах от фактического размера)
class ImageLayer(QWidget):
    def __init__(self, imagePath: str, width: int, height: int, parent: QWidget) -> None:
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

    # Функция задания картинки из потока байтов. Вызывается родительским классом при открытии проекта
    def setBits(self, bits: bytes) -> None:
        self.image = QImage(data=bits)

    # Функция загрузки картинки из файла. Вызывается самим классом при выборе картинки через панель инструментов
    def setImage(self, imagePath: str) -> None:
        self.image = QImage(imagePath)
        self.image = self.image.scaled(self.image.width() * self.size / 100, self.image.height() * self.size / 100,
                                       aspectRatioMode=Qt.IgnoreAspectRatio)

    # Функция нахождения ограничивающих линий прямоугольника, в котором картинка лежит. Возвращает индексы линий в
    # соответствующих подсписках в списке self.gridLines. Используется самим классом при отрисовке
    def findBoundaryGridLines(self, x1: int, y1: int, x2: int, y2: int) -> tuple:
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

    # Функция отрисовки прямоугольника из линий сетки, в котором картинка лежит. Рисуется только когда пользователь
    # рисует (для удобства предпросмотра). Фактически является вынесенной частью функции self.paintEvent
    def drawGridRect(self, painter: QPainter) -> None:
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
                    QBrush(QColor(0, 0, 255, alpha=64)))

    # Функция отрисовки содержимого слоя. Преобразует ограничивающие линии сетки в заданные абсолютно, далее, в
    # зависимости от типа выравнивания, вычисляет левую верхнюю точку картинки и рисует саму картинку
    def paintEvent(self, event: QPaintEvent) -> None:
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

    # Функция преобразования линии сетки в отступ от левого верхнего края (в пикселях), используется при нахождении
    # ограничивающего прямоугольника линий сетки и отрисовке слоя. Подробнее о формате аргументов см. в комментарии
    # к самому классу
    def gridLineToOffset(self, direction: int, indentType: int, indent: int) -> int:
        return int(self.resolution[direction ^ 1] / 100 * indent) if indentType == 1 else indent

    # Обновление слоя извне при изменении состояния панели инструментов пользователем
    def updateState(self, size: int, alignment: str, tool: str) -> None:
        self.tool = tool
        self.alignment = alignment
        self.size = size

        self.setImage(self.imagePath)
        self.repaint()

    # Обновления картинки слоя извне при выборе новой картинки пользователем на панели инструментов
    def updateImage(self, imagePath: str) -> None:
        self.setImage(imagePath)
        self.imagePath = imagePath

        self.repaint()

    # Обработчик нажатия кнопки мыши. Если слой неактивен, но находится поверх остальных (имеет наибольший z),
    # то event будет приходить ему. В таком случае слой через self.parent передает нажатие на нужный слой.
    # В противном случае включается self.drawing и обновляется self.lastMousePos (при задании и оффсета, и
    # прямоугольника он используется)
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

            self.repaint()
        elif not self.active and self.parent.currentLayer != -1:
            self.parent.scene.items()[self.parent.currentLayer].widget().mouseMoveEvent(event)

    # Обработчик отпускания кнопки мыши. Если слой неактивен, но находится поверх остальных (имеет наибольший z),
    # то event будет приходить ему. В таком случае слой через self.parent передает нажатие на нужный слой.
    # В противном случае проверяется, идет ли сейчас рисование. Если да, то оно заканчивается, => надо переопределить
    # прямоугольник сетки, если пользователь хотел это сделать, тогда он находится заново, и слой отрисовывается
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
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

    # Задание нового разрешения. Вызывается родительским классом Window при изменении разрешения проекта
    # параметр stretch ничего не задаёт, так как картинка в любом случае должна подгоняться под обновлённую сетку
    def setResolution(self, width: int, height: int, stretch: bool):
        self.setMinimumSize(width, height)
        self.setMaximumSize(width, height)
        self.resolution = width, height
        self.repaint()
