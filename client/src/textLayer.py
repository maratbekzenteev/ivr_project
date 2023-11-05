from PyQt5.QtWidgets import QWidget, QTextEdit, QFrame
from PyQt5.QtGui import QColor, QPalette, QBrush, QPainter, QFont, QMouseEvent, QPaintEvent
from PyQt5.QtCore import QPoint, Qt, QRect, pyqtSlot


# Класс текстового слоя. Сигналов не сообщает
# Графические элементы:
# - self.textEdit - QTextEdit, редактируемое поле ввода
# Атрибуты:
# - self.parent - QWidget, родительский виджет главного окна, через который слой получает информацию о сетке и
# - - обновляет панель инструментов
# - self.resolution - tuple(int, int), кортеж из ширины и высоты слоя, а равно и всего проекта
# - self.color - QColor, цвет выделенных и новых символов
# - self.font - str, шрифт выделенных и новых символов
# - self.size - int, размер шрифта выделенных и новых символов, принимает значения от 1 до 256
# - self.fontWeight - QFont::Weight, задаёт жирность выделенных и новых символов,
# - - принимает значения:
# - - - QFont.Normal - нежирный
# - - - QFont.DemiBold - полужирный
# - self.italic - bool, задаёт курсивность выделенных и новых символов
# - self.underline - bool, задаёт подчёркнутость выделенных и новых символов
# - self.alignment - Qt::AlignmentFlag, задаёт выравнивание текста, принимает значения:
# - - Qt.AlignLeft - выравнивание по левому краю
# - - Qt.AlignCenter - выравнивание по ценрту
# - - Qt.AlignRight - выравниваение по правому краю
# - - Qt.AlignJustify - выравнивание по всей ширине
# - self.active - bool, True - слой активирован (доступен для изменения), False - слой деактивирован
# - self.drawing - bool, когда пользователь нажимает кнопку мысли за пределами прямоугольника self.textEdit, считается,
# - - что он рисует и может менять ограничительный прямоугольник содержимого слоя
# - self.curMousePos - QPoint, первая точка, задающая прямоугольник, в котором будет лежать картинка, "рисуемый" сейчас
# - self.lastMousePos - QPoint, вторяя точка, задающая прямоугольник, в котором будет лежать картинка, "рисуемый" сейчас
# - self.previousZValue - int. Поскольку self.textEdit никак не реагирует на нажатие, передаваемое ему вручную,
# - - было решено при каждой активации двигать слой на высоту 1023, а при деактивации - обратно на настоящую высоту.
# - - Чтобы настоящая высота была легко доступка программе, она хранится как атрибут
# - self.gridLines - list(list(tuple(int, int))) - список линий сетки. Под индеком 0 - горизонтальные, 1 - вертикальные.
# - - В каждом подсписке линия сетки задаётся как tuple(indentType, indent), где indentType - тип отступа линии
# - - от верхнего (для горизонтальных) или левого (для вертикальных) края, значения:
# - - - 0 - абсолютный отступ (задаётся в пикселях переменной indent)
# - - - 1 - относительный отступ (задаётся в процентах от высоты (для горизонтальных) или ширины (для вертикальных)
# - - - - изображения переменной indent)
# - self.leftBorder - tuple(indentType, indent), левая сторона прямоугольника, задаётся описанным выше образом
# - self.rightBorder - tuple(indentType, indent), правая сторона прямоугольника, задаётся описанным выше образом
# - self.topBorder - tuple(indentType, indent), верхняя сторона прямоугольника, задаётся описанным выше образом
# - self.bottomBorder - tuple(indentType, indent), нижняя сторона прямоугольника, задаётся описанным выше образом
class TextLayer(QWidget):
    def __init__(self, width: int, height: int, parent: QWidget) -> None:
        super().__init__()
        self.parent = parent

        self.setMinimumSize(width, height)
        self.setMaximumSize(width, height)
        self.resolution = width, height

        self.textEdit = QTextEdit(self)
        self.textEdit.setGeometry(0, 0, 0, 0)
        self.textEdit.setFrameShape(QFrame.NoFrame)
        self.textEdit.setStyleSheet('background: rgba(0,0,0,0%)')

        self.color = QColor(0, 0, 0)
        self.font = 'Verdana'
        self.size = 32
        self.fontWeight = QFont.Weight.Normal
        self.italic = False
        self.underline = False
        self.alignment = Qt.AlignLeft
        self.textEdit.setFont(QFont('Verdana', 32))
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

    # Функция преобразования линии сетки в отступ от левого верхнего края (в пикселях), используется при нахождении
    # ограничивающего прямоугольника линий сетки и отрисовке слоя. Подробнее о формате аргументов см. в комментарии
    # к самому классу
    def gridLineToOffset(self, direction: int, indentType: int, indent: int) -> int:
        return int(self.resolution[direction ^ 1] / 100 * indent) if indentType == 1 else indent

    # Функция нахождения ограничивающих линий прямоугольника, в котором плашка с текстом лежит. Возвращает индексы линий
    # в соответствующих подсписках в списке self.gridLines. Используется самим классом при отрисовке
    def findBoundaryGridLines(self, x1: int, y1: int, x2: int, y2: int):
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

    # Функция отрисовки слоя. Поскольку self.textEdit рисуется сам, здесь отрисовываются только вспомогательные элементы
    # а именно прямоугольник, которым ограничена плашка с текстом (если слой активен), прямоугольник,
    # рисуемый пользователем, и назначаемый пользователем новый ограничивающий прямоугольник, если пользователь рисует
    def paintEvent(self, event: QPaintEvent) -> None:
        qp = QPainter(self)
        if self.active:
            x1 = self.gridLineToOffset(1, *self.leftBorder)
            x2 = self.gridLineToOffset(1, *self.rightBorder)
            y1 = self.gridLineToOffset(0, *self.topBorder)
            y2 = self.gridLineToOffset(0, *self.bottomBorder)
            qp.setPen(Qt.DashLine)
            qp.drawRect(QRect(QPoint(x1, y1), QPoint(x2, y2)))

        self.drawGridRect(qp)

    # Обработчик нажатия кнопки мыши. Если нажатие поступило в обработку, значит, оно было сделано вне self.textEdit,
    # а значит, если слой активен, то пользователь пытается перенаначить прямоугольник, в котором плашка с текстом
    # лежит. Тогда сохраняется первая точка нажатия пользователя. Если слой неактивен, то нажатие сообщается активному
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self.active:
            self.drawing = True
            self.lastMousePos = event.pos()
            self.curMousePos = event.pos()

            self.gridLines = [self.parent.scene.items()[1].widget().hLines,
                              self.parent.scene.items()[1].widget().vLines]
        elif self.parent.currentLayer != -1:
            self.parent.scene.items()[self.parent.currentLayer].widget().mousePressEvent(event)

    # Обработчик движения мыши. Если слой неактивен, то движение сообщается активному слою. Иначе, если пользователь
    # перезадаёт ограничивающий прямоугольник плашки с текстом, обновляется вторая задающая точка прямоугольника,
    # который пользователь рисует (из которого потом программа вычислит ограничивающий прямоугольник)
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.active and self.drawing:
            self.curMousePos = event.pos()

            self.repaint()
        elif not self.active and self.parent.currentLayer != -1:
            self.parent.scene.items()[self.parent.currentLayer].widget().mouseMoveEvent(event)

    # Обработчик отпускания кнопки мыши. Если слой неактивен, то отпускание сообщается активному слою. Иначе, если
    # пользователь рисовал, рисование прекращается, и на основе нарисованного пользователем прямоугольника вычисляется
    # ограничительный прямоугольник для плашки с текстом. Позиция плашки подгоняется под новый прямоугольник
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
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

            self.updateTextEdit()
        elif not self.active and self.parent.currentLayer != -1:
            self.parent.scene.items()[self.parent.currentLayer].widget().mouseMoveEvent(event)

    # Обновление атрибута self.previousZValue при активации слоя для последующего восстановления z из него при
    # последующей деактивации
    def storeZValue(self, z: int) -> None:
        self.previousZValue = z

    # Обновление слоя извне после изменения пользователем состояния панели инструментов
    def updateState(self, color: QColor, font: str, size: int, fontWeight: QFont.Weight,
                    italic: bool, underline: bool, alignment: Qt.AlignmentFlag) -> None:
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

    # Обновление атрибутов слоя изнутри после перемещения курсора для последующего обновления панели инструментов
    @pyqtSlot()
    def updateFromNewCursorPosition(self):
        self.color = self.textEdit.textColor()
        self.font = self.textEdit.font().key()
        self.size = self.textEdit.fontPointSize()
        self.fontWeight = self.textEdit.fontWeight()
        self.italic = self.textEdit.fontItalic()
        self.underline = self.textEdit.fontUnderline()
        self.alignment = self.textEdit.alignment()

        self.parent.updateTextToolbarState()

    # Обновление координат self.textEdit после повторного задания пользователем ограничивающего прямоугольника
    def updateTextEdit(self):
        x1 = self.gridLineToOffset(1, *self.leftBorder)
        x2 = self.gridLineToOffset(1, *self.rightBorder)
        y1 = self.gridLineToOffset(0, *self.topBorder)
        y2 = self.gridLineToOffset(0, *self.bottomBorder)
        self.textEdit.setGeometry(x1, y1, x2 - x1, y2 - y1)
        self.textEdit.show()
        self.repaint()

    # Задание нового разрешения. Вызывается родительским классом Window при изменении разрешения проекта
    # параметр stretch ничего не задаёт, так как плашка с текстом должна подгоняться под обновлённую сетку
    def setResolution(self, width, height, stretch):
        self.setMinimumSize(width, height)
        self.setMaximumSize(width, height)
        self.resolution = width, height
        self.updateTextEdit()
        self.repaint()
