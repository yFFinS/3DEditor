import functools
from _weakref import ref

import glm
from OpenGL import GL
from PyQt5.QtCore import Qt, QObject
from PyQt5.QtOpenGL import QGLWidget
from PyQt5.QtWidgets import QMainWindow, QWidget, QSplitter, QHBoxLayout, QSizePolicy, QVBoxLayout, QLineEdit, QLabel

from core.event_dispatcher import *
from core.interfaces import UpdateReceiverInterface
from gui.interfaces import GLSceneInterface, SceneExplorerInterface
from gui.widgets import SceneActions, SceneObjectList
from interaction.camera_controller import CameraController
from interaction.geometry_builders import PointBuilder, LineBuilder, PlaneBuilder
from render.shaders import ShaderProgram
from scene.camera import Camera
from scene.render_geometry import SceneGrid, SceneCoordAxis
from scene.scene import Scene
from scene.scene_object import SceneObject

from shared import EditorShared


class Window(QMainWindow):
    def __init__(self):
        super(QMainWindow, self).__init__()

        self.__editor = EditorGUI()

        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('Файл')

        self.setCentralWidget(self.__editor)
        self.setWindowTitle('3D Editor')

    def closeEvent(self, a0):
        self.__editor.closeEvent(a0)


class EditorGUI(QWidget):
    def __init__(self):
        super(EditorGUI, self).__init__()
        self.__action_splitter = QSplitter(Qt.Vertical)
        self.__main_splitter = QSplitter(Qt.Horizontal)

        self.__gl_widget = GLScene()
        self.__scene_exp = SceneExplorer(self.__gl_widget)
        self.__scene_act = SceneActions(self.__gl_widget)

        self.__action_splitter.addWidget(self.__scene_act)
        self.__action_splitter.addWidget(self.__main_splitter)

        self.__main_splitter.addWidget(self.__scene_exp)
        self.__main_splitter.addWidget(self.__gl_widget)
        self.__main_splitter.setSizes([self.__scene_exp.width(), 200])

        self.__action_splitter.setStyleSheet("QSplitter::handle { background-color: gray }")
        self.__main_splitter.setStyleSheet("QSplitter::handle { background-color: gray }")

        layout = QHBoxLayout()
        layout.addWidget(self.__action_splitter)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def closeEvent(self, event):
        self.__gl_widget.unload()


class GLScene(QGLWidget, GLSceneInterface):
    def __init__(self):
        super(QGLWidget, self).__init__()
        self.__program = None
        self.__scene = Scene()
        self.__camera_controller = None
        self.__last_action = None
        self.__geometry_builder = None

        size_pol = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        size_pol.setVerticalStretch(1)
        size_pol.setHorizontalStretch(1)
        size_pol.setControlType(QSizePolicy.Frame)
        self.setSizePolicy(size_pol)

        self.installEventFilter(self)

    def __subscribe_to_scene(self):
        self.__scene.on_object_added += self.__update_internal
        self.__scene.on_object_removed += self.__update_internal
        self.__scene.on_objects_selected += self.__update_internal
        self.__scene.on_objects_deselected += self.__update_internal

    def __update_internal(self, *args, **kwargs):
        self.update()

    def redraw(self):
        self.update()

    def get_scene(self):
        return self.__scene

    def initializeGL(self):
        GL.glClearColor(170 / 256, 170 / 256, 170 / 256, 1)
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        GL.glPointSize(6)
        GL.glLineWidth(1)
        GL.glEnable(GL.GL_LINE_SMOOTH)

        self.__program = ShaderProgram("shaders/default.vert", "shaders/default.frag")
        print(self.parent())
        self.__scene.camera = Camera(self.width(), self.height())
        self.__camera_controller = CameraController(self.__scene.camera)

        SceneObject.SHADER_PROGRAM = self.__program

        self.__scene.add_object(SceneGrid())
        self.__scene.add_object(SceneCoordAxis())

        self.update()

    def resizeGL(self, w, h):
        if w <= 0 or h <= 0:
            return
        GL.glViewport(0, 0, w, h)
        self.__scene.camera.width = w
        self.__scene.camera.height = h

    def paintGL(self):
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        self.__scene.render()

    def eventFilter(self, obj: QObject, event: QEvent):
        update = dispatch(self.__camera_controller, event)
        if self.__geometry_builder is not None:
            update |= dispatch(self.__geometry_builder, event)

        if update:
            self.update()

        if self.__geometry_builder is not None or event.type() != QEvent.MouseButtonPress:
            return super(QGLWidget, self).eventFilter(obj, event)

        event = QMouseEvent(event)
        if event.button() == Qt.LeftButton:
            self.try_select_scene_object(event)
        return super(QGLWidget, self).eventFilter(obj, event)

    def unload(self):
        self.__scene.unload()
        self.__program.dispose()

    def no_action(self):
        self.__geometry_builder = None
        self.__last_action = self.no_action

    def move_object(self):
        # TODD:
        self.__geometry_builder = None
        self.__last_action = self.move_object

    def create_point(self):
        self.__geometry_builder = PointBuilder(self.__scene)
        self.__subscribe_to_geometry_builder()
        self.__last_action = self.create_point

    def create_line(self):
        self.__geometry_builder = LineBuilder(self.__scene)
        self.__subscribe_to_geometry_builder()
        self.__last_action = self.create_line

    def create_plane(self):
        self.__geometry_builder = PlaneBuilder(self.__scene)
        self.__subscribe_to_geometry_builder()
        self.__last_action = self.create_plane

    def __subscribe_to_geometry_builder(self):
        self.__geometry_builder.on_builder_ready += self.__on_builder_ready
        self.__geometry_builder.on_builder_canceled += self.__on_builder_canceled

    def __on_builder_ready(self):
        self.__geometry_builder = None
        self.__last_action()

    def __on_builder_canceled(self):
        self.__on_builder_ready()

    def handle_move_object(self, event):
        # TODO:
        pass

    def try_select_scene_object(self, event: QMouseEvent):
        x, y = event.x(), event.y()
        to_select = self.__scene.find_selectable(glm.vec2(x, y))

        mods = event.modifiers()

        if not to_select or not Qt.ShiftModifier & mods:
            self.__deselect_all()
        if to_select:
            self.__scene.select(to_select)

        self.update()

    def __deselect_all(self):
        selected_objs = list(self.__scene.objects)
        self.__scene.deselect(selected_objs)


class SceneExplorer(QWidget, SceneExplorerInterface):
    def __init__(self, gl_scene: GLSceneInterface):
        super(SceneExplorer, self).__init__()

        self.__gl_scene = ref(gl_scene)

        layout = QVBoxLayout()
        self.__list = SceneObjectList(gl_scene)

        self.__props = SceneObjectProperties(gl_scene)

        layout.addWidget(self.__props)
        layout.addWidget(self.__list)

        self.setLayout(layout)

        size_pol = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        size_pol.setVerticalStretch(1)
        size_pol.setControlType(QSizePolicy.Frame)
        self.setSizePolicy(size_pol)
        self.setMinimumSize(300, 200)
        self.setMaximumWidth(500)

    def add_scene_object(self, scene_object: SceneObject):
        self.__list.add_object(scene_object)

    def clear_selection(self):
        self.__list.__deselect_all()

    def select_scene_object(self, scene_object, deselect_others=False):
        if deselect_others:
            self.__list.__deselect_all()
        self.set_scene_object_selected(scene_object, True)

    def deselect_scene_object(self, scene_object: SceneObject):
        self.set_scene_object_selected(scene_object, False)

    def set_scene_object_selected(self, scene_object: SceneObject, value: bool):
        self.__list.__set_object_selected(scene_object, value)


class SceneObjectProperties(QWidget):
    def __init__(self, gl_scene: GLSceneInterface):
        super(SceneObjectProperties, self).__init__()

        self.__gl_scene = ref(gl_scene)
        self.__subscribe_to_scene()

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.__selected_counter = 0
        self.__scene_object = None
        self.__object_name_edit = QLineEdit()
        layout.addWidget(self.__object_name_edit)

        self.__xyz = QWidget()
        xyz_layout = QHBoxLayout()
        xyz_layout.setContentsMargins(0, 0, 0, 0)

        self.x_edit = QLineEdit()
        self.y_edit = QLineEdit()
        self.z_edit = QLineEdit()
        self.x_edit.editingFinished.connect(self.update_object)
        self.y_edit.editingFinished.connect(self.update_object)
        self.z_edit.editingFinished.connect(self.update_object)

        x_name_edit_pair = QWidget()
        x_layout = QHBoxLayout()
        x_layout.setContentsMargins(0, 0, 0, 0)
        x_layout.addWidget(QLabel("x:"))
        x_layout.addWidget(self.x_edit)
        x_name_edit_pair.setLayout(x_layout)

        y_name_edit_pair = QWidget()
        y_layout = QHBoxLayout()
        y_layout.setContentsMargins(0, 0, 0, 0)
        y_layout.addWidget(QLabel("y:"))
        y_layout.addWidget(self.y_edit)
        y_name_edit_pair.setLayout(y_layout)

        z_name_edit_pair = QWidget()
        z_layout = QHBoxLayout()
        z_layout.setContentsMargins(0, 0, 0, 0)
        z_layout.addWidget(QLabel("z:"))
        z_layout.addWidget(self.z_edit)
        z_name_edit_pair.setLayout(z_layout)

        xyz_layout.addWidget(x_name_edit_pair)
        xyz_layout.addWidget(y_name_edit_pair)
        xyz_layout.addWidget(z_name_edit_pair)

        self.__xyz.setLayout(xyz_layout)
        layout.addWidget(self.__xyz)

        size_pol = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        size_pol.setVerticalStretch(1)

    def __subscribe_to_scene(self):
        scene = self.__gl_scene().get_scene()
        scene.on_objects_selected += self.__on_objects_selected
        scene.on_objects_deselected += self.__on_objects_deselected

    def __on_objects_selected(self, scene_objects):
        if self.__selected_counter == 1:
            self.__set_object(scene_objects[0])
        else:
            self.clear_and_disable_edit()

    def __on_objects_deselected(self, scene_objects):
        if self.__scene_object is not None and self.__scene_object in scene_objects:
            self.clear_and_disable_edit()

    def clear_and_disable_edit(self):
        self.__scene_object = None
        self.x_edit.setText("")
        self.y_edit.setText("")
        self.z_edit.setText("")
        self.__xyz.setDisabled(True)

    def __set_object(self, scene_object: SceneObject):
        self.__scene_object = scene_object
        self.__xyz.setEnabled(True)
        self.update_properties()

    def update_properties(self):
        pos = self.__scene_object.transform.translation
        self.x_edit.setText(f'{pos.x:.4f}')
        self.y_edit.setText(f'{pos.y:.4f}')
        self.z_edit.setText(f'{pos.z:.4f}')

    def update_object(self):
        try:
            pos = glm.vec3(float(self.x_edit.text()),
                           float(self.y_edit.text()),
                           float(self.z_edit.text()))
            self.__scene_object.set_position(pos)
            self.__gl_scene().redraw()
        except ValueError:
            self.update_properties()
