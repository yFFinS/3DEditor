from PyQt5.QtCore import pyqtSignal, QPoint, QSize, Qt
from PyQt5.QtGui import QColor, QImage
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QWidget, QLabel
from PyQt5.QtOpenGL import QGLWidget

import sys
from shaders import ShaderProgram

from scenes import Scene
import OpenGL.GL as GL
from helpers import *


class Window(QWidget):
    def __init__(self):
        super(Window, self).__init__()

        self.__glWidget = GLWidget()

        self.__mainLayout = QHBoxLayout()
        self.__mainLayout.addWidget(self.__glWidget)

        label = QLabel()
        label.setText("Amogus")

        self.__mainLayout.addWidget(label)
        self.setLayout(self.__mainLayout)

        self.setWindowTitle('Test window')

    def closeEvent(self, event):
        self.__glWidget.unload()
        event.accept()


class GLWidget(QGLWidget):
    def __init__(self, parent=None):
        super(GLWidget, self).__init__(parent)
        self.__program = None
        self.__scene = Scene()

    def sizeHint(self):
        return QSize(800, 640)

    def initializeGL(self):
        GL.glClearColor(0.1, 0.1, 0.2, 1)
        self.__program = ShaderProgram("shaders/default.vert", "shaders/default.frag")
        pos = to_float32_array([0, 1, 0, 1, 0, 0, -1, 0, 0])
        ind = to_uint32_array([0, 1, 2])
        obj = self.__scene.create_object()
        obj.set_shader_program(self.__program)
        obj.set_positions(pos)
        obj.set_indices(ind)

    def resizeGL(self, w: int, h: int):
        if w <= 0 or h <= 0:
            return
        GL.glViewport(0, 0, w, h)

    def paintGL(self):
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)
        self.__scene.render()

    def unload(self):
        self.__scene.unload()
        self.__program.dispose()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
