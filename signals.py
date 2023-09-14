from PyQt5.QtCore import pyqtSignal, QObject


# Класс сигналов, используемых практически всеми эл-ами панелей инструментов.
# Передаются обычно сначала от эл-а интерфейса к панели инструментов, затем к классу Window
class Signals(QObject):
    valueChanged = pyqtSignal()


# Специальные сигналы для классов LayerList и LayerListItem. Выделены в отдельный класс, чтобы
# главный цикл программы не пытался считывать эти сигналы с эл-ов, которые их по определению иметь не могут
# Аргумент(ы) - int, индекс(ы) слоя(слоев) в индексации self.currentLayer
class LayerSignals(QObject):
    # Слой активирован
    activated = pyqtSignal(int)
    # Слой деактивирован
    deactivated = pyqtSignal(int)
    # Слой сделан видимым
    shown = pyqtSignal(int)
    # Слой скрыт
    hidden = pyqtSignal(int)
    # Слой подвинут на 1 "уровень" выше
    movedUp = pyqtSignal(int)
    # Слой подвинут на 1 "уровень" ниже
    movedDown = pyqtSignal(int)
    # Два слоя (теоретически, не обязательно соседние) были поменяны местами
    swappedLayers = pyqtSignal(int, int)


class GridSignals(QObject):
    # h/v, indentType, val
    added = pyqtSignal(int, int, int)
    # h/v, indentType, val
    deleted = pyqtSignal(int, int, int)


class ImageSignals(QObject):
    # size, alignment, tool
    stateChanged = pyqtSignal(int, str, str)
    imageChanged = pyqtSignal(str)
