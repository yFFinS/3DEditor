from PyQt5.QtCore import QObject
from PyQt5.QtGui import QWindow, QOpenGLContext, QSurfaceFormat
from PyQt5.QtOpenGL import QGLWidget, QGLFormat
from PyQt5.QtWidgets import QMainWindow, QWidget, QSplitter, QHBoxLayout, \
    QSizePolicy, QVBoxLayout, QLineEdit, QLabel, QShortcut

from core.event_dispatcher import *
from gui.interfaces import GLSceneInterface, SceneExplorerInterface
from gui.widgets import SceneActions, SceneObjectList
from interaction.camera_controller import CameraController
from interaction.geometry_builders import *
from render.shaders import ShaderProgram
from scene.camera import Camera
from scene.render_geometry import SceneGrid, SceneCoordAxis
from scene.scene import Scene
from scene.scene_object import SceneObject


class Window(QMainWindow):
    def __init__(self):
        super(Window, self).__init__()
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

        self.__action_splitter.setStyleSheet(
            "QSplitter::handle { background-color: gray }")
        self.__main_splitter.setStyleSheet(
            "QSplitter::handle { background-color: gray }")

        layout = QHBoxLayout()
        layout.addWidget(self.__action_splitter)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def closeEvent(self, event):
        self.__gl_widget.unload()


class GLScene(QGLWidget, GLSceneInterface, EventHandlerInterface):
    def __init__(self):
        sur_format = QGLFormat()
        sur_format.setSamples(4)
        sur_format.setProfile(QGLFormat.CoreProfile)

        # noinspection PyTypeChecker
        super(QGLWidget, self).__init__(sur_format)

        self.__scene = Scene()
        self.__camera_controller = None
        self.__last_action = None
        self.__geometry_builder = None
        self.__initialized = False
        self.__shaders = []

        size_pol = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        size_pol.setVerticalStretch(1)
        size_pol.setHorizontalStretch(1)
        size_pol.setControlType(QSizePolicy.Frame)
        self.setSizePolicy(size_pol)
        self.installEventFilter(self)

        self.__delete_sc = QShortcut("Del", self)
        self.__delete_sc.activated.connect(self.__delete_selected_objects)
        self.__cancel_sc = QShortcut("Esc", self)
        self.__cancel_sc.activated.connect(self.__cancel)

    def __cancel(self):
        if self.__geometry_builder is not None and self.__geometry_builder.has_any_progress:
            self.__geometry_builder.cancel()
        else:
            self.__scene.deselect([obj for obj in self.__scene.objects if obj.selected])
        self.update()

    def __subscribe_to_scene(self):
        self.__scene.on_object_added += self.__redraw_internal
        self.__scene.on_object_removed += self.__redraw_internal
        self.__scene.on_objects_selected += self.__redraw_internal
        self.__scene.on_objects_deselected += self.__redraw_internal

    def __redraw_internal(self, *args, **kwargs):
        self.redraw()

    def redraw(self):
        self.update()

    def get_scene(self):
        return self.__scene

    def initializeGL(self):
        GL.glClearColor(170 / 256, 170 / 256, 170 / 256, 1)
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glEnable(GL.GL_POINT_SMOOTH)
        GL.glEnable(GL.GL_LINE_SMOOTH)
        GL.glEnable(GL.GL_MULTISAMPLE)
        GL.glEnable(GL.GL_POLYGON_OFFSET_FILL)
        GL.glPolygonOffset(1, 1)

        self.__shaders = [ShaderProgram("shaders/default.vert", "shaders/default.frag"),
                          ShaderProgram("shaders/point.vert", "shaders/default.frag"),
                          ShaderProgram("shaders/line.vert", "shaders/default.frag"),
                          ShaderProgram("shaders/triangle.vert", "shaders/default.frag")]

        RawSceneObject.SHADER_PROGRAM = self.__shaders[0]
        ScenePoint.SHADER_PROGRAM = self.__shaders[1]

        SceneLine.SHADER_PROGRAM = self.__shaders[2]
        SceneEdge.SHADER_PROGRAM = self.__shaders[2]

        ScenePlane.SHADER_PROGRAM = self.__shaders[3]
        SceneFace.SHADER_PROGRAM = self.__shaders[3]

        self.__scene.camera = Camera(self.width(), self.height())
        self.__camera_controller = CameraController(self.__scene.camera)

        self.__scene.add_object(SceneGrid())
        self.__scene.add_object(SceneCoordAxis())

        self.__initialized = True

    def eventFilter(self, a0: 'QObject', a1: 'QEvent') -> bool:
        redraw = dispatch(self, a1)
        if redraw:
            self.redraw()
        return super(GLScene, self).eventFilter(a0, a1)

    def resizeGL(self, w, h):
        if w <= 0 or h <= 0:
            return
        GL.glViewport(0, 0, w, h)
        self.__scene.camera.width = w
        self.__scene.camera.height = h

    def paintGL(self):
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        self.__scene.render()

    def on_mouse_pressed(self, event: QMouseEvent):
        if self.__geometry_builder is not None:
            return False
        if event.button() == Qt.LeftButton:
            return self.try_select_scene_object(event)
        return False

    def __delete_selected_objects(self):
        for obj in filter(lambda o: o.selected, list(self.__scene.objects)):
            self.__scene.remove_object(obj)
        self.redraw()

    def on_any_event(self, event: QEvent):
        if not self.__initialized:
            return False
        update = dispatch(self.__camera_controller, event)
        if self.__geometry_builder is not None:
            update |= dispatch(self.__geometry_builder, event)
        if update:
            self.update()

    def unload(self):
        self.__scene.unload()
        for shader in self.__shaders:
            shader.dispose()
        self.__shaders.clear()

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

    def create_edge(self):
        self.__geometry_builder = EdgeBuilder(self.__scene)
        self.__subscribe_to_geometry_builder()
        self.__last_action = self.create_edge

    def create_face(self):
        self.__geometry_builder = FaceBuilder(self.__scene)
        self.__subscribe_to_geometry_builder()
        self.__last_action = self.create_face

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
        self.resize(300, 200)
        self.setMaximumWidth(700)

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

        self.__selected_objects = []
        self.__scene_object = None
        self.__object_name_edit = QLineEdit()
        self.__object_name_edit.editingFinished.connect(self.update_object)
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

        self.__clear_and_disable_edit()

    def __subscribe_to_scene(self):
        scene = self.__gl_scene().get_scene()
        scene.on_objects_selected += self.__on_objects_selected
        scene.on_objects_deselected += self.__on_objects_deselected

    def __on_objects_selected(self, scene_objects):
        self.__selected_objects.extend(scene_objects)
        self.__object_name_edit.setText(str(len(self.__selected_objects)))
        if len(self.__selected_objects) == 1:
            self.__set_object(self.__selected_objects[0])
        else:
            self.__clear_and_disable_edit()

    def __on_objects_deselected(self, scene_objects):
        self.__selected_objects = \
            [selected for selected in self.__selected_objects
             if selected not in scene_objects]
        self.__object_name_edit.setText(str(len(self.__selected_objects)))
        if len(self.__selected_objects) == 1:
            self.__set_object(self.__selected_objects[0])
        else:
            self.__clear_and_disable_edit()

    def __clear_and_disable_edit(self):
        self.__scene_object = None
        self.__object_name_edit.clear()
        self.__object_name_edit.setDisabled(True)
        self.x_edit.clear()
        self.y_edit.clear()
        self.z_edit.clear()
        self.__xyz.setDisabled(True)

    def __set_object(self, scene_object: SceneObject):
        self.__scene_object = scene_object
        self.__xyz.setEnabled(True)
        self.__object_name_edit.setEnabled(True)
        self.update_properties()

    def update_properties(self):
        if self.__scene_object is None:
            return
        prim = self.__scene_object.primitive
        if prim is not None:
            self.__object_name_edit.setText(prim.name)
        pos = self.__scene_object.transform.translation
        self.x_edit.setText(f'{pos.x:4f}')
        self.y_edit.setText(f'{pos.y:4f}')
        self.z_edit.setText(f'{pos.z:4f}')

    def update_object(self):
        try:
            name = self.__object_name_edit.text()
            pos = glm.vec3(float(self.x_edit.text()),
                           float(self.y_edit.text()),
                           float(self.z_edit.text()))
            prim = self.__scene_object.primitive
            if prim is not None:
                self.__scene_object.primitive.name = name
                self.__scene_object.post_update()
            self.__scene_object.update_position(pos)
            self.__gl_scene().redraw()
        except ValueError:
            self.update_properties()
