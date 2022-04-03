from PyQt5.QtCore import QSize, QEvent, QObject
from PyQt5.QtGui import QKeyEvent, QMouseEvent
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QWidget, QLabel
from PyQt5.QtOpenGL import QGLWidget

import sys
from shaders import ShaderProgram

from scenes import *
import OpenGL.GL as GL
from helpers import *


class Window(QWidget):
    def __init__(self):
        super(Window, self).__init__()

        self.__glWidget = GlSceneWidget()

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


class GlSceneWidget(QGLWidget):
    def __init__(self, parent=None):
        super(GlSceneWidget, self).__init__(parent)
        self.__program = None
        self.__scene = Scene()
        self.__camera_controller = None

        self.installEventFilter(self)
        self.grabKeyboard()
        self.grabMouse()

    def sizeHint(self):
        return QSize(800, 640)

    def initializeGL(self):
        GL.glClearColor(0.1, 0.5, 0.6, 1)
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        self.__program = ShaderProgram("shaders/default.vert", "shaders/default.frag")
        self.__scene.camera = Camera(self.width(), self.height())
        self.__camera_controller = CameraController(self.__scene.camera)

        pos = np.array([glm.vec3(0, 1, 0),
                        glm.vec3(1, 0, 0),
                        glm.vec3(-1, 0, 0)])
        col = np.array([glm.vec4(1, 0, 0.5, 0.5),
                        glm.vec4(0, 0, 1, 0.5),
                        glm.vec4(0, 1, 0, 0.5)])
        ind = to_uint32_array([0, 1, 2])

        mesh = Mesh()
        mesh.set_indices(ind)
        mesh.set_positions(pos)
        mesh.set_colors(col)

        obj = self.__scene.create_object()
        obj.mesh = mesh
        obj.shader_program = self.__program

    def resizeGL(self, w: int, h: int):
        if w <= 0 or h <= 0:
            return
        GL.glViewport(0, 0, w, h)

    def paintGL(self):
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)
        self.__scene.render()

    def eventFilter(self, a0: QObject, a1: QEvent):
        match a1.type():
            case QEvent.KeyPress:
                self.__camera_controller.handle_key_press(self, QKeyEvent(a1))
            case QEvent.MouseButtonPress:
                self.__camera_controller.handle_mouse_press(self, QMouseEvent(a1))
            case QEvent.MouseButtonRelease:
                self.__camera_controller.handle_mouse_release(self, QMouseEvent(a1))
            case QEvent.MouseMove:
                self.__camera_controller.handle_mouse_move(self, QMouseEvent(a1))
            case QEvent.Close:
                self.__scene.unload()
                self.__program.dispose()
        return super(QGLWidget, self).eventFilter(a0, a1)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
