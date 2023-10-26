from PyQt5.QtGui import QColor


class State:
    def __init__(self):
        self.bitmapColor = QColor(0, 0, 0)
        self.bitmapWidth = 1
        self.bitmapTool = 'none'

        self.imageAlignment = 'cntr'
        self.imageTool = 'none'

        self.shapeType = 'line'
        self.shapeWidth = 1
        self.shapeColor = QColor(0, 0, 0)
        self.shapeTool = 'none'

        self.textStyle = {}
        self.textFont = ''
        self.textSize = 16
        self.textTool = 'none'
