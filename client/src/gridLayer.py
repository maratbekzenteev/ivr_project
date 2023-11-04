from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QColor, QPainter, QPalette, QBrush, QPaintEvent
from PyQt5.QtCore import Qt


# Класс слоя сетки. В проекте имеет z=1024, дабы отображаться выше всех слоёв (на практике их не может быть столько)
# Сигналов не сообщает. Изменение этого слоя проходит через панель инструментов GridToolbar (см. client.gui.gridToolbar)
# Атрибуты:
# - self.width - int, ширина изображения слоя (а равно, и всего проекта)
# - self.height - int, высота изображения слоя (а равно, и всего проекта)
# - self.active - bool, True - слой активирован (доступен для изменения), False - слой деактивирован. Слой сетки
# - - может быть активирован только посредством дебаггинга, так как не может быть активирован через список слоёв,
# - - так как является статическим и меняется только через панель инструментов GridToolbar
# - self.hLines - list(tuple(int, int)) - список горизонтальных линий сетки. Каждое значение в списке - кортеж,
# - - задаваемый как (indentType, indent), где indentType - тип отступа линии сетки от верхнего края, значения:
# - - - 0 - абсолютный отступ (задаётся в пикселях переменной indent)
# - - - 1 - относительный отступ (задаётся в процентах от высоты изображения переменной indent)
# - self.vLines - list(tuple(int, int)) - список вертикальных линий сетки. Каждое значение в списке - кортеж,
# - - задаваемый как (indentType, indent), где indentType - тип отступа линии сетки от левого края, значения:
# - - - 0 - абсолютный отступ (задаётся в пикселях переменной indent)
# - - - 1 - относительный отступ (задаётся в процентах от ширины изображения переменной indent)
class GridLayer(QWidget):
    # Инициализация атрибутов, задание разрешения, изменение фона на прозрачный
    def __init__(self, width: int, height: int) -> None:
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

    # Добавление новой линии сетки. Вызывается родительским классом после добавления линии через панель инструментов.
    # В качестве аргументов передаются direction - направление линии сетки (0 - горизонтальное, 1 - вертикальное),
    # indentType - тип отступа, indent - отступ (подробности в комментарии к самому классу)
    def addLine(self, direction: int, indentType: int, indent: int) -> None:
        if direction == 0:
            self.hLines.append((indentType, indent))
        elif direction == 1:
            self.vLines.append((indentType, indent))

        self.sort()
        self.repaint()

    # Добавление новой линии сетки. Вызывается родительским классом после удаления линии через панель инструментов.
    # В качестве аргументов передаются direction - направление линии сетки (0 - горизонтальное, 1 - вертикальное),
    # indentType - тип отступа, indent - отступ (подробности в комментарии к самому классу)
    # (!) Функция работает за линейное время от количества линий сетки
    def deleteLine(self, direction: int, indentType: int, indent: int) -> None:
        if direction == 0:
            self.hLines.remove((indentType, indent))
        elif direction == 1:
            self.vLines.remove((indentType, indent))

        self.repaint()

    # Сортировка списков линий сетки. Проводится при каждом добавлении новой линии. Это нужно для того, чтобы
    # слои-картинки, фигурные слои и текстовые слои, которым эти списки передаются для корректной отрисовки по линиям
    # сетки, быстрее искали прямоугольник, в котором лежит их содержимое
    # (!) Функия работает за O(n*log(n)) от количества линий сетки
    def sort(self) -> None:
        self.hLines.sort(key=lambda x: x[1] if x[0] == 0 else self.height / 100 * x[1])
        self.vLines.sort(key=lambda x: x[1] if x[0] == 0 else self.width / 100 * x[1])

    # Отрисовка линий сетки по одной. Каждая из них, в силу z=1024, рисуется выше содержимого любого другого слоя
    # (!) Функция работает за линейное время от количества линий сетки
    def paintEvent(self, event: QPaintEvent) -> None:
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

    # Задание нового разрешения. Вызывается родительским классом Window при изменении разрешения проекта
    # параметр stretch ничего не задаёт, так как сетка в любом случае должна подгоняться под новое разрешение
    def setResolution(self, width: int, height: int, stretch: bool) -> None:
        self.width, self.height = width, height
        self.sort()
        self.repaint()
