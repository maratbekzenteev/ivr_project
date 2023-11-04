from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QPalette, QColor


# Виджет цветной кнопки, унаследованный от QPushButton. Используемые сигналы: self.clicked.
# По поведению идентичен QPushButton
# Атрибуты:
# - self.color - QColor, нужен для быстрого доступа к цвету кнопки со стороны панели инструментов
class ColoredButton(QPushButton):
    # Инициализация родительского класса и косметические изменения относительно него, инициализация атрибута
    def __init__(self, color) -> None:
        super().__init__()

        self.setMinimumSize(8, 8)
        self.setMaximumSize(128, 128)

        self.color = color

        palette = self.palette()
        palette.setColor(QPalette.Button, color)
        self.setFlat(True)
        self.setAutoFillBackground(True)
        self.setPalette(palette)
        self.repaint()

    # Функция изменения цвета кнопки извне
    def setColor(self, color: QColor) -> None:
        palette = self.palette()
        palette.setColor(QPalette.Button, color)
        self.setPalette(palette)
        self.repaint()
