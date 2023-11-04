from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPixmap, QPainter, QPaintEvent
from PyQt5.QtCore import Qt


# Класс фонового слоя. Сигналов не сообщает
# Атрибуты:
# - self.active - bool, определяет, является ли слой выделенным (в случае с этим типом слоёв не играет никакой роли, ибо
# - - слой статический)
# - self.pixmap - QPixmap, фоновое изображение, необходимо, чтобы фон был отличим, например, от белой заливки
class BackgroundLayer(QWidget):
    # Инициализация атрибутов, задание разрешения, изменение фона на прозрачный
    def __init__(self, width, height) -> None:
        super().__init__()

        self.setMinimumSize(width, height)
        self.setMaximumSize(width, height)

        self.active = False

        self.pixmap = QPixmap("../../checkerboard.png").scaled(width, height, aspectRatioMode=Qt.IgnoreAspectRatio)

    # Отрисовка слоя
    def paintEvent(self, event: QPaintEvent) -> None:
        qp = QPainter(self)
        qp.drawPixmap(0, 0, self.pixmap)

    # Задание нового разрешения. Вызывается родительским классом Window при изменении разрешения проекта
    # параметр stretch ничего не задаёт, ибо фоновое изображение всегда должно заполнять всю рабочую область
    def setResolution(self, width: int, height: int, stretch: bool) -> None:
        self.setMinimumSize(width, height)
        self.setMaximumSize(width, height)
        self.pixmap = QPixmap("../../checkerboard.png").scaled(width, height, aspectRatioMode=Qt.IgnoreAspectRatio)
        self.repaint()
