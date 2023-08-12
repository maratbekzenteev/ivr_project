from PyQt5.QtWidgets import (QApplication, QGraphicsScene, QGraphicsView, QTabWidget, QLabel, QToolButton, QVBoxLayout,
                             QWidget, QListWidget, QPushButton, QGridLayout, QShortcut, QSpinBox, QSlider, QColorDialog,
                             QLineEdit)
from PyQt5.QtGui import QPixmap, QFont, QKeySequence, QPalette, QBrush, QColor, QPainter, QPen, QIcon
from PyQt5.QtCore import Qt, QRect, pyqtSignal, QObject, QSize
from colorsys import hsv_to_rgb, rgb_to_hsv

# В этом файле описаны классы элементов графического интерфейса программы,
# унаследованных от стандартных элементов QtWidgets


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


# Виджет панели инструментов для работы с растровыми слоями. Набор сигналов - Signals
# Графические элементы:
# - self.layout - QGridLayout, сетка выравнивания виджетов в панели
# - self.colorPicker - ColorPicker, палитра со стандартными цветами
# - self.colorPreview - ColorPreview, индикатор текущего выбранного цвета с кнопкой выбора другого цвета (не из палитры)
# - self.widthSlider - QSlider - ползунок выбора толщины (ширины) кисти/карандаша/ручки, принимает значения от 1 до 32
# - self.toolSelector - ToolSelector, выбор текущего инструмента для работы со слоем
# Аттрибуты:
# - self.color - QColor, цвет заливки, кисти, карандаша, ручки, прямоугольника, прямой, эллипса
# - self.width - int, толщина кисти, карандаша, ручки, прямоугольника, эллипса, прямой
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
class BitmapToolbar(QWidget):
    # Инициализация интерфейса, подключение сигналов к слотам, объявление аттрибутов класса
    def __init__(self):
        super().__init__()

        self.layout = QGridLayout(self)
        self.setLayout(self.layout)

        self.signals = Signals()

        self.color = QColor(0, 0, 0)
        self.colorPicker = ColorPicker()
        self.colorPicker.signals.valueChanged.connect(self.updateValues)
        self.colorPreview = ColorPreview()
        self.colorPreview.signals.valueChanged.connect(self.updateValues)

        self.width = 1
        self.widthSlider = QSlider()
        self.widthSlider.setMinimum(1)
        self.widthSlider.setMaximum(32)
        self.widthSlider.valueChanged.connect(self.updateValues)

        self.tool = 'none'
        self.toolSelector = ToolSelector('Кисть', 'Ручка', 'Карандаш', 'Прямая', 'Прямоугольник', 'Эллипс', 'Заливка')
        self.toolSelector.setIcons(*(['tmp_icon.png'] * 7))
        self.toolSelector.setStates('brsh', 'pen', 'penc', 'line', 'rect', 'oval', 'fill')
        self.toolSelector.signals.valueChanged.connect(self.updateValues)

        self.layout.addWidget(self.colorPicker, 0, 0)
        self.layout.addWidget(self.colorPreview, 0, 1)
        self.layout.addWidget(self.widthSlider, 0, 2)
        self.layout.addWidget(WidthPictogram(), 0, 3)
        self.layout.addWidget(self.toolSelector, 0, 4)

    # Обновление состояния класса. Слот для сигналов valueChanged элементов графического интерфейса.
    # Если цвета self.colorPreview, self.colorPicker и self.color не совпадают, значит, цвет был изменен.
    # Цвет всех эл-ов меняется на самый новый, т.е. на тот, который имеет лишь 1 из 3 эл-ов.
    # Также обновляется толщина и инструмент. Сообщается сигнал valueChanged
    def updateValues(self):
        if self.colorPreview.color != self.color:
            self.color = self.colorPreview.color
            self.colorPicker.setColor(self.color)
        elif self.colorPicker.color != self.color:
            self.color = self.colorPicker.color
            self.colorPreview.setColor(self.color)

        self.width = self.widthSlider.value()
        self.tool = self.toolSelector.state
        self.signals.valueChanged.emit()


# Виджет палитры (25 цветов в ширину, 5 цветов в высоту) для выбора цвета. Набор сигналов - Signals
# Цвета, размещенные в каждой из ячеек палитры, реализованы классом ColoredButton
# Графические элементы:
# - self.layout - QGridLayout, сетка выравнивания ColoredButton в палитре
# - Объекты класса ColoredButton, на каждый по 1 цвету
# Аттрибуты:
# - self.color - QColor, текущий цвет
class ColorPicker(QWidget):
    # Инициализация аттрибутов, соединение сигналов со слотами, размещение ColoredButton в ячейки сетки
    def __init__(self):
        super().__init__()

        self.signals = Signals()

        self.layout = QGridLayout(self)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.color = QColor(0, 0, 0)

        for red in range(5):
            for green in range(5):
                for blue in range(5):
                    self.layout.addWidget(
                        ColoredButton(QColor(min(255, red * 64), min(255, green * 64), min(255, blue * 64))),
                        red, green * 5 + blue
                    )
                    self.layout.itemAtPosition(red, green * 5 + blue).widget().clicked.connect(self.updateColor)

    # Функция для обновления цвета извне (например, когда пользователь обновил цвет через ColorPreview)
    def setColor(self, color: QColor) -> None:
        self.color = color

    # Обновление цвета при нажатии ColoredButton, слот сигнала ColoredButton.clicked.
    # Сообщает сигнал self.signals.valueChanged
    def updateColor(self):
        self.color = self.sender().color
        self.signals.valueChanged.emit()


# Виджет цветной кнопки, унаследованный от QPushButton. Используемые сигналы: self.clicked.
# По поведению идентичен QPushButton
# Аттрибуты:
# - self.color - QColor, нужен для быстрого доступа к цвету кнопки со стороны панели инструментов
class ColoredButton(QPushButton):
    # Инициализация родительского класса и косметические изменения относительно него, инициализация аттрибута
    def __init__(self, color):
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


# Виджет просмотра текущего цвета с функцией его изменения с помощью QColorDialog. Набор сигналов - Signals.
# Графические элементы:
# - self.layout - QGridLayout, сетка выравнивания элементов виджета
# - self.colorButton - ColoredButton, кнопка, выступающая в роли индикатора текущего цвета
# - self.colorDialog - QColorDialog, диалог выбора цвета (отдельное окно), которого нет в палитре
# - self.chooseColorButton - QPushButton, кнопка для показа self.colorDialog
# Аттрибуты:
# - self.color - текущий цвет
class ColorPreview(QWidget):
    # Инициализация графических элементов, подключение сигналов к слотам, инициализация аттрибута
    def __init__(self):
        super().__init__()

        self.layout = QGridLayout(self)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)

        self.signals = Signals()

        self.color = QColor(0, 0, 0)
        self.colorButton = ColoredButton(QColor(0, 0, 0))

        self.colorDialog = QColorDialog()
        self.colorDialog.setOption(QColorDialog.ShowAlphaChannel, on=True)
        self.colorDialog.colorSelected.connect(self.chooseColor)

        self.chooseColorButton = QPushButton('Другой цвет')
        self.chooseColorButton.clicked.connect(self.showDialog)

        self.layout.addWidget(self.colorButton, 0, 0)
        self.layout.addWidget(self.chooseColorButton, 1, 0)

    # Обработчик отображения диалога self.colorDialog, слот сигнала self.chooseColorButton.clicked
    def showDialog(self):
        self.colorDialog.show()
        self.colorDialog.setCurrentColor(self.color)

    # Обработкик диалога self.colorDialog после нажатия пользователем кнопки "ОК".
    # Слот сигнала self.colorDialog.colorSelected. Обновляет цвет self.colorButton согласно новым данным,
    # сообщает сигнал valueChanged
    def chooseColor(self):
        self.color = self.colorDialog.selectedColor()
        self.colorButton.setColor(self.color)

        self.signals.valueChanged.emit()

    # Функция обновления цвета извне, например, при выборе цвета пользователем через ColorPicker
    def setColor(self, color: QColor) -> None:
        self.color = color
        self.colorButton.setColor(color)


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


# Виджет выбора инструмента. Отличается от обычной таблицы с кнопками тем, что кнопка отпускается сама
# при нажатии другой кнопки, но при бездействии остается нажатой, а при повторном нажатии отпускается.
# Набор сигналов - Signals
# Графические элементы:
# - self.layout - QGridLayout, сетка для выравнивания QToolButton
# - QToolButton, размещенные в сетке
# Аттрибуты:
# - self.buttonToState - dict(str, str), ключи - тексты на кнопках, значения - соответствующие им значения self.state
# - self.state - str, текущее состояние, соответствующее выбранному инструменту ('none', если инструмент не выбран)
class ToolSelector(QWidget):
    # Инициализация графических элементов, соединение сигналов и слотов, определение названий и кол-ва кнопок
    def __init__(self, *button_names: str) -> None:
        super().__init__()

        self.signals = Signals()

        self.layout = QGridLayout(self)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)

        self.buttonToState = dict()
        self.state = 'none'

        for i in range(len(button_names)):
            self.layout.addWidget(QToolButton(), 0, i)
            self.layout.itemAtPosition(0, i).widget().setText(button_names[i])
            self.layout.itemAtPosition(0, i).widget().clicked.connect(self.updateState)
            self.layout.itemAtPosition(0, i).widget().setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            self.layout.itemAtPosition(0, i).widget().setAutoRaise(True)
            self.layout.itemAtPosition(0, i).widget().setCheckable(True)
            self.layout.itemAtPosition(0, i).widget().setIconSize(QSize(96, 96))

    # Определение словаря self.buttonToState, в аргументах передаются названия состояний,
    # соответствующих каждой из кнопок в порядке слева направо. К-во состояний не должно превышать к-во кнопок,
    # определенных при инициализации
    def setStates(self, *states: str) -> None:
        for i in range(len(states)):
            self.buttonToState[self.layout.itemAtPosition(0, i).widget().text()] = states[i]

    # Присвоение кнопкам иконок, названия которых перечислены в аргументах в порядке следованя кнопок слева направо
    def setIcons(self, *icons):
        for i in range(len(icons)):
            self.layout.itemAtPosition(0, i).widget().setIcon(QIcon('tmp_icon.png'))

    # Обновление состояния при нажатии одной из кнопок. Слот сигнала self.layout.itemAtPosition(0, i).widget().clicked
    # Сообщает сигнал valueChanged
    def updateState(self):
        if self.sender().isChecked():
            self.state = self.buttonToState[self.sender().text()]

            for i in range(len(self.buttonToState)):
                self.layout.itemAtPosition(0, i).widget().setChecked(False)
            self.sender().setChecked(True)

        else:
            self.state = 'none'

        self.signals.valueChanged.emit()


# Виджет панели инструментов по созданию слоев. Сам по себе не сообщает сигналов, привязан к слотам в классе окна
# Графические элементы:
# - self.layout - QGridLayout, сетка выравнивания кнопок в панели
# - self.newBitmapLayerButton - QToolButton, кнопка создания растрового слоя
# - self.newShapeLayerButton - QToolButton, кнопка создания фигурного слоя
class LayerToolbar(QWidget):
    # Инициализация графических элементов
    def __init__(self):
        super().__init__()

        self.layout = QGridLayout(self)
        self.setLayout(self.layout)

        self.newBitmapLayerButton = QToolButton()
        self.newBitmapLayerButton.setText('Новый растровый слой')
        self.newBitmapLayerButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.newBitmapLayerButton.setAutoRaise(True)
        self.newBitmapLayerButton.setIconSize(QSize(64, 64))
        self.newBitmapLayerButton.setIcon(QIcon('tmp_icon.png'))

        self.newShapeLayerButton = QToolButton()
        self.newShapeLayerButton.setText('Новый фигурный слой')
        self.newShapeLayerButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.newShapeLayerButton.setAutoRaise(True)
        self.newShapeLayerButton.setIconSize(QSize(64, 64))
        self.newShapeLayerButton.setIcon(QIcon('tmp_icon.png'))

        self.layout.addWidget(self.newBitmapLayerButton, 0, 0, alignment=Qt.AlignLeft)
        self.layout.addWidget(self.newShapeLayerButton, 1, 0, alignment=Qt.AlignLeft)


# Виджет отображения слоя в списке слоев. Помимо прочего позволяет сделать слой текущим (активировать),
# подвинуть выше/ниже относительно других слоев, скрыть/показать слой. Необходим для размещения в LayerList.
# Набор сигналов - LayerSignals
# Графические элементы:
# - self.layout - QGridLayout, сетка для выравнивания графических элементов виджета
# - self.activateButton - QPushButton, кнопка активации слоя. Повторное нажатие деактивирует слой,
# - - так что ни один слой не выделен
# - self.nameField - QLineEdit, изменяемое название слоя.
# - - Программой не используется, необходимо для удобства пользователя
# - self.upButton - QPushButton, кнопка перемещения слоя на уровень выше. Если слой уже выше всех, ничего не происходит
# - self.downButton - QPushButton, кнопка перемещения слоя на уровень ниже. Если слой ниже всех, ничего не происходит
# - self.hideButton - QPushButton, кнопка скрытия/показа слоя
# Аттрибуты:
# - self.z - int, высота слоя, т.е. положение по оси аппликат. Определяет отображение слоя над/под другими слоями.
# - - Чем больше self.z, тем "ближе к экрану" слой
# - self.index - int, индекс слоя в индексации Window.currentLayer, т.е. индекс слоя в self.index на 1 меньше
# - - индекса в Window.scene
# - self.type - str, тип слоя (растровый, фигурный, ...). Принимает значения:
# - - 'bmp' - растровый
# - self.visible - bool, True - слой отображается (видим), False - слой скрыт
# - self.active - bool, True - слой активен (его можно редактировать, он текущий), False - слой деактивирован
class LayerListItem(QWidget):
    # Инициализация графических элементов, подключение сигналов к слотам, инициализация аттрибутов
    def __init__(self, name: str, type: str, z: int, index: int):
        super().__init__()

        self.layout = QGridLayout(self)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)

        self.signals = LayerSignals()

        self.z = z
        self.index = index
        self.type = type
        self.visible = True
        self.active = False

        self.activateButton = QPushButton('⌘')
        self.activateButton.clicked.connect(self.activate)

        self.nameField = QLineEdit(name)

        self.upButton = QPushButton('Выше')
        self.upButton.clicked.connect(self.moveUp)

        self.downButton = QPushButton('Ниже')
        self.downButton.clicked.connect(self.moveDown)

        self.hideButton = QPushButton('Глаз')
        self.hideButton.clicked.connect(self.changeVisibility)

        self.layout.addWidget(self.activateButton, 0, 0, 2, 1, Qt.AlignLeft)
        self.layout.addWidget(self.nameField, 0, 1, 1, 3, Qt.AlignCenter)
        self.layout.addWidget(self.upButton, 1, 1)
        self.layout.addWidget(self.downButton, 1, 2)
        self.layout.addWidget(self.hideButton, 1, 3)

        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setBrush(QPalette.Window, QBrush(QColor(0, 0, 0, alpha=0), Qt.SolidPattern))
        self.setPalette(palette)

    # Функция обновления внешнего вида виджета (например, при активации). Фон активного виджета светло-синий,
    # неактивного - серый в цвет окна. У скрытого слоя надписи серые, у видимого - белые.
    # Изменения внешнего вида производятся через изменение QPalette виджета
    def updatePalette(self):
        palette = self.palette()
        palette.setBrush(QPalette.Window, QBrush(QColor(
            0, 0, 255, alpha=64) if self.active else QColor(0, 0, 0, alpha=0), Qt.SolidPattern))
        palette.setBrush(QPalette.Text, QBrush(QColor(
            0, 0, 0) if self.visible else QColor(0, 0, 0, alpha=128), Qt.SolidPattern))
        self.setPalette(palette)

    # Обработчик нажатия self.activateButton, слот сигнала self.activateButton.clicked.
    # Если виджет уже активен, деакивирует его с сообщением сигнала deactivated, если нет,
    # активирует с сообщением сигнала activated. Затем согласно изменениям обновляется внешний вид виджета
    def activate(self):
        if self.active:
            self.signals.deactivated.emit(self.index)
            self.active = False
        else:
            self.signals.activated.emit(self.index)
            self.active = True

        self.updatePalette()

    # Обработчик нажатия self.hideButton, слот сигнала self.hideButton.clicked.
    # Если виджет уже скрыт, делает его видимым с сообщением сигнала shown, если нет,
    # скрывает с сообщением сигнала hidden. Затем согласно изменениям обновляется внешний вид виджета
    def changeVisibility(self):
        if self.visible:
            self.signals.hidden.emit(self.index)
            self.visible = False
        else:
            self.signals.shown.emit(self.index)
            self.visible = True

        self.updatePalette()

    # Слот сигнала self.moveUpButton.clicked. Сообщает сигнал movedUp. Вся работа по перемещению слоя
    # осуществляется в LayerList и Window
    def moveUp(self):
        self.signals.movedUp.emit(self.index)

    # Слот сигнала self.moveDownButton.clicked. Сообщает сигнал movedDown. Вся работа по перемещению слоя
    # осуществляется в LayerList и Window
    def moveDown(self):
        self.signals.movedDown.emit(self.index)


# Виджет списка слоёв для удобной манипуляции (скрытия, перемещения по высоте, ...) пользователем.
# Набор сигналов - LayerSignals. Поддерживает те же переменные для контроля к-ва и положения слоёв,
# что и Window, для удобства обращения к ним.
# Графические элементы:
# - self.layout - QVBoxLayout, выравнивает объекты LayerListItem по сетке, причем в порядке снизу вверх.
# - - Это сделано, чтобы новые слои добавлялись сверху, а не снизу: так пользователю легче понять, что слой выше всех
# - Объекты класса LayerListItem, в которых поддерживается вся необходимая информация о каждом слое в отдельности
# Аттрибуты:
# - self.hightestZ - int, класс, поддерживающий самое высокое значение self.z у любого из слоёв за все время
# - - (т.е. удаленные слои тоже считаются). Это нужно для нахождения "безопасного" значения self.z для нового слоя
# - self.layerCount - int, текущее к-во слоев
class LayerList(QWidget):
    # Инициализация графических элементов и аттрибутов
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setDirection(QVBoxLayout.BottomToTop)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)

        self.signals = LayerSignals()

        self.highestZ = 0
        self.layerCount = 0

        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setBrush(QPalette.Window, QBrush(QColor(255, 255, 255), Qt.SolidPattern))
        self.setPalette(palette)

    # Функция добавления нового растрового слоя. Добавляет слой выше остальных (на передний план),
    # обновляет переменные состояния, подключает сигналы к слотам
    def newBitmapLayer(self):
        self.layout.addWidget(LayerListItem(
            f'Растровый слой ' + str(self.highestZ + 1), 'bmp', self.highestZ, self.layerCount))
        self.layerCount += 1
        self.highestZ += 1
        self.layout.itemAt(self.layerCount - 1).widget().signals.activated.connect(self.activateLayer)
        self.layout.itemAt(self.layerCount - 1).widget().signals.deactivated.connect(self.deactivateLayer)
        self.layout.itemAt(self.layerCount - 1).widget().signals.shown.connect(self.showLayer)
        self.layout.itemAt(self.layerCount - 1).widget().signals.hidden.connect(self.hideLayer)
        self.layout.itemAt(self.layerCount - 1).widget().signals.movedUp.connect(self.moveUpLayer)
        self.layout.itemAt(self.layerCount - 1).widget().signals.movedDown.connect(self.moveDownLayer)

    # Активация слоя. Слот сигнала LayerListItem.activated. Итерируется по всем слоям и деактивирует, обновляя графику
    # (хранить индекс активированного слоя не на сцене, а в списке нецелесообразно в условиях адекватного к-ва слоев).
    # Сообщает сигнал activated. Необходимости итерироваться снова в поисках активированного виджета по индексу на сцене
    # не требуется, так как LayerListItem умеет это делать сам уже после сообщения сигнала
    def activateLayer(self, index: int) -> None:
        for i in range(self.layerCount):
            self.layout.itemAt(i).widget().active = False
            self.layout.itemAt(i).widget().updatePalette()

        self.signals.activated.emit(index)

    # Дективация слоя. Слот сигнала LayerListItem.deactivated. Итерируется по всем слоям и деактивирует, обновляя
    # (хранить индекс активированного слоя не на сцене, а в списке нецелесообразно в условиях адекватного к-ва слоев).
    # Сообщает сигнал deactivated
    def deactivateLayer(self, index: int) -> None:
        for i in range(self.layerCount):
            self.layout.itemAt(i).widget().active = False
            self.layout.itemAt(i).widget().updatePalette()

        self.signals.deactivated.emit(index)

    # Слот сигнала LayerListItem.shown. Сообщает сигнал shown, сам не делает ничего, так как внешний вид виджет
    # обновляет сам, а показ на сцене осуществляет класс Window
    def showLayer(self, index: int) -> None:
        self.signals.shown.emit(index)

    # Слот сигнала LayerListItem.hidden. Сообщает сигнал hidden, сам не делает ничего, так как внешний вид виджет
    # обновляет сам, а скрытие на сцене осуществляет класс Window
    def hideLayer(self, index: int) -> None:
        self.signals.hidden.emit(index)

    # Функция перемещения слоя выше в списке. Слот сигнала LayerListItem.movedUp
    def moveUpLayer(self, index: int) -> None:
        # Слой с таким индексом на сцене ищется среди всех за линейное время
        inListIndex = -1
        for i in range(self.layerCount):
            if self.layout.itemAt(i).widget().index == index:
                inListIndex = i
                break

        # Если слой и так выше всех, то есть имеет наибольший возможный индекс в списке, нельзя переместить => выходим
        if inListIndex == self.layerCount - 1:
            return

        # Далее меняются местами свойства найденного LayerListItem и того, что выше него на 1 (имеет больший на 1 индекс
        # в списке). Местами меняются именно свойства, а не сами объекты, так как Qt не предоставляет возможности
        # сделать это, не затрагивая другие виджеты

        # Через вспомогательные переменные меняются местами имена слоев
        aName = self.layout.itemAt(inListIndex).widget().nameField.text()
        bName = self.layout.itemAt(inListIndex + 1).widget().nameField.text()
        self.layout.itemAt(inListIndex).widget().nameField.setText(bName)
        self.layout.itemAt(inListIndex + 1).widget().nameField.setText(aName)

        # Распаковкой кортежа меняются местами высоты слоев
        self.layout.itemAt(inListIndex).widget().z, self.layout.itemAt(inListIndex + 1).widget().z = \
            self.layout.itemAt(inListIndex + 1).widget().z, self.layout.itemAt(inListIndex).widget().z

        # Распаковкой кортежа меняются местами индексы слоев на сцене
        self.layout.itemAt(inListIndex).widget().index, self.layout.itemAt(inListIndex + 1).widget().index = \
            self.layout.itemAt(inListIndex + 1).widget().index, self.layout.itemAt(inListIndex).widget().index

        # Распаковкой кортежа меняются местами типы слоев
        self.layout.itemAt(inListIndex).widget().type, self.layout.itemAt(inListIndex + 1).widget().type = \
            self.layout.itemAt(inListIndex + 1).widget().type, self.layout.itemAt(inListIndex).widget().type

        # Распаковкой кортежа меняются местами аттрибуты видимости слоев
        self.layout.itemAt(inListIndex).widget().visible, self.layout.itemAt(inListIndex + 1).widget().visible = \
            self.layout.itemAt(inListIndex + 1).widget().visible, self.layout.itemAt(inListIndex).widget().visible

        # Распаковкой кортежа меняются местами аттрибуты активности слоев
        self.layout.itemAt(inListIndex).widget().active, self.layout.itemAt(inListIndex + 1).widget().active = \
            self.layout.itemAt(inListIndex + 1).widget().active, self.layout.itemAt(inListIndex).widget().active

        # Внешний вид LayerListItem обновляется согласно новым данным
        self.layout.itemAt(inListIndex).widget().updatePalette()
        self.layout.itemAt(inListIndex + 1).widget().updatePalette()

        # Сигналом swappedLayers сообщается необходимость поменять 2 слоя местами на сцене
        self.signals.swappedLayers.emit(index, self.layout.itemAt(inListIndex).widget().index)

    # Функция перемещения слоя ниже в списке. Слот сигнала LayerListItem.movedDown
    def moveDownLayer(self, index: int) -> None:
        # Слой с таким индексом на сцене ищется среди всех за линейное время
        inListIndex = -1
        for i in range(self.layerCount):
            if self.layout.itemAt(i).widget().index == index:
                inListIndex = i
                break

        # Если слой и так ниже всех, то есть имеет наименьший возможный индекс в списке, нельзя переместить => выходим
        if inListIndex == 0:
            return

        # Далее меняются местами свойства найденного LayerListItem и того, что ниже него на 1 (имеет меньший на 1 индекс
        # в списке). Местами меняются именно свойства, а не сами объекты, так как Qt не предоставляет возможности
        # сделать это, не затрагивая другие виджеты

        # Через вспомогательные переменные меняются местами имена слоев
        aName = self.layout.itemAt(inListIndex).widget().nameField.text()
        bName = self.layout.itemAt(inListIndex - 1).widget().nameField.text()
        self.layout.itemAt(inListIndex).widget().nameField.setText(bName)
        self.layout.itemAt(inListIndex - 1).widget().nameField.setText(aName)

        # Распаковкой кортежа меняются местами высоты слоев
        self.layout.itemAt(inListIndex).widget().z, self.layout.itemAt(inListIndex - 1).widget().z = \
            self.layout.itemAt(inListIndex - 1).widget().z, self.layout.itemAt(inListIndex).widget().z

        # Распаковкой кортежа меняются местами индексы слоев на сцене
        self.layout.itemAt(inListIndex).widget().index, self.layout.itemAt(inListIndex - 1).widget().index = \
            self.layout.itemAt(inListIndex - 1).widget().index, self.layout.itemAt(inListIndex).widget().index

        # Распаковкой кортежа меняются местами типы слоев
        self.layout.itemAt(inListIndex).widget().type, self.layout.itemAt(inListIndex - 1).widget().type = \
            self.layout.itemAt(inListIndex - 1).widget().type, self.layout.itemAt(inListIndex).widget().type

        # Распаковкой кортежа меняются местами аттрибуты видимости слоев
        self.layout.itemAt(inListIndex).widget().visible, self.layout.itemAt(inListIndex - 1).widget().visible = \
            self.layout.itemAt(inListIndex - 1).widget().visible, self.layout.itemAt(inListIndex).widget().visible

        # Распаковкой кортежа меняются местами аттрибуты активности слоев
        self.layout.itemAt(inListIndex).widget().active, self.layout.itemAt(inListIndex - 1).widget().active = \
            self.layout.itemAt(inListIndex - 1).widget().active, self.layout.itemAt(inListIndex).widget().active

        # Внешний вид LayerListItem обновляется согласно новым данным
        self.layout.itemAt(inListIndex).widget().updatePalette()
        self.layout.itemAt(inListIndex - 1).widget().updatePalette()

        # Сигналом swappedLayers сообщается необходимость поменять 2 слоя местами на сцене
        self.signals.swappedLayers.emit(index, self.layout.itemAt(inListIndex).widget().index)
