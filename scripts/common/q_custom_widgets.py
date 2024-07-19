import numpy as np
from PyQt5 import QtCore, QtWidgets


class MainWidget(QtWidgets.QWidget):
    # Allows reacting to key events (unless a textbox has focus)
    keyPressed = QtCore.pyqtSignal(int)
    
    def __init__(self, master):
        super().__init__(master)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        
    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        self.keyPressed.emit(event.key())


class MySlider(QtWidgets.QSlider):
    # Sets the slider to the position where the mouse clicked instead of just doing a big step
    def __init__(self):
        super().__init__(QtCore.Qt.Horizontal)
        self.mousePressPos = None
        self.setMouseTracking(True)
        
    def wheelEvent(self, e):
        self.setValue(self.value() + np.sign(e.angleDelta().y()) * self.singleStep())
    
    def mousePressEvent(self, e):
        if e.button() == QtCore.Qt.LeftButton:
            self.mousePressPos = e.pos()
        else:
            super().mousePressEvent(e)
    
    def mouseMoveEvent(self, e):
        if self.mousePressPos is not None and e.buttons() & QtCore.Qt.LeftButton:
            self.update_from_mouse_pos(e)
        else:
            super().mouseMoveEvent(e)
    
    def mouseReleaseEvent(self, e):
        if  self.mousePressPos is not None \
        and e.button() == QtCore.Qt.LeftButton \
        and e.pos() in self.rect():
            self.update_from_mouse_pos(e)
            self.mousePressPos = None
        else:
            return super().mouseReleaseEvent(e)

    def update_from_mouse_pos(self, e):
        e.accept()
        x = e.pos().x()
        value = (self.maximum() - self.minimum()) * x / self.width() + self.minimum()
        self.setValue(int(value))
        