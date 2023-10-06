from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPen, QColor
from PyQt5.QtCore import Qt


# Виджет, отображающийся рядом с ползунком толщины для большей понятности назначения ползунка пользователю.
# С другими виджетами не взаимодействует, сигналы не сообщает
class WidthPictogram(QWidget):
    # Инициализация как виджета, ограничение размеров
    def __init__(self):
        super().__init__()
        self.setMaximumSize(32, 256)
        self.setMinimumSize(16, 32)

    # Изменение отображения так, чтобы рисовалась "пиктограмма толщины"
    def paintEvent(self, event):
        qp = QPainter(self)
        height = self.geometry().height()
        width = self.geometry().width()
        for i in range(16):
            qp.setPen(QPen(QColor(0, 0, 0), 16 - i, Qt.SolidLine, Qt.RoundCap, Qt.BevelJoin))
            qp.drawPoint(width // 2, i * height // 16)
