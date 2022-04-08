import numpy as np
from PyQt5.QtCore import QSize, QEvent, QObject
from PyQt5.QtGui import QKeyEvent, QMouseEvent
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QWidget, QLabel, QMenuBar, QMenu, QMainWindow, QAction
from PyQt5.QtOpenGL import QGLWidget

import sys
from shaders import ShaderProgram

from scenes import *
import OpenGL.GL as GL
from helpers import *
from gui import *
from render_geometry import *


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(500, 300, 1000, 600)

        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('Файл')
        sceneMenu = menuBar.addMenu('Сцена')

        createPointAction = QAction("Создать точку", self)
        sceneMenu.addAction(createPointAction)

        self.__editor = EditorGUI()
        self.setCentralWidget(self.__editor)

        self.setWindowTitle('Test window')

    def closeEvent(self, a0):
        self.__editor.closeEvent(a0)


class EditorGUI(QWidget):
    def __init__(self):
        super(EditorGUI, self).__init__()

        self.__glWidget = GlSceneWidget(self)
        self.__mainLayout = QHBoxLayout()
        self.__mainLayout.addWidget(SceneExplorer())
        self.__mainLayout.addWidget(self.__glWidget)

        self.setLayout(self.__mainLayout)

    def closeEvent(self, a0):
        self.__glWidget.unload()


class GlSceneWidget(QGLWidget):
    def __init__(self, parent=None):
        super(GlSceneWidget, self).__init__(parent)
        self.__program = None
        self.__scene = Scene()
        self.__camera_controller = None

        self.installEventFilter(self)

    def sizeHint(self):
        return QSize(800, 640)

    def initializeGL(self):
        GL.glClearColor(0.1, 0.5, 0.6, 1)
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        GL.glPointSize(5)
        GL.glLineWidth(2)

        self.__program = ShaderProgram("shaders/default.vert", "shaders/default.frag")
        self.__scene.camera = Camera(self.width(), self.height())
        self.__camera_controller = CameraController(self.__scene.camera)

        point1 = ScenePoint(Point(1, 1, 1))
        point1.shader_program = self.__program
        self.__scene.add_object(point1)
        point2 = ScenePoint(Point(5, 1, 1))
        point2.shader_program = self.__program
        self.__scene.add_object(point2)

        line = SceneLine(LineBy2Points(point1.point, point2.point))
        line.shader_program = self.__program
        self.__scene.add_object(line)

    def resizeGL(self, w, h):
        if w <= 0 or h <= 0:
            return
        GL.glViewport(0, 0, w, h)
        self.__scene.camera.width = w
        self.__scene.camera.height = h

    def paintGL(self):
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
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
        return super(QGLWidget, self).eventFilter(a0, a1)

    def unload(self):
        self.__scene.unload()
        self.__program.dispose()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
