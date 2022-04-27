import OpenGL.GL
from interfaces import *
from PyQt5.QtCore import QSize, QEvent, QObject, Qt
from PyQt5.QtGui import QFont, QPalette, QKeyEvent, QMouseEvent, QWheelEvent
from PyQt5.QtWidgets import (QVBoxLayout, QListWidgetItem, QLineEdit,
                             QHBoxLayout, QWidget, QLabel, QMainWindow,
                             QAction, QListWidget, QAbstractItemView, QPushButton, QSizePolicy, QSplitter, QFrame)
from PyQt5.QtOpenGL import QGLWidget

from scene import *
from render_geometry import *
from shared import EditorShared
from camera import Camera, CameraController
from geometry_builder import *


class Window(QMainWindow):
    def __init__(self):
        super(QMainWindow, self).__init__()

        EditorShared.init(EditorGUI())

        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('Файл')

        self.setCentralWidget(self.editor)
        self.setWindowTitle('3D Editor')

    @property
    def editor(self):
        return EditorShared.get_editor()

    def closeEvent(self, a0):
        self.editor.closeEvent(a0)


class SceneActions(QWidget, SceneActionsInterface):
    def __init__(self, editor):
        super(SceneActions, self).__init__()

        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(layout)

        self.__editor = ref(editor)
        self.__buttons = []

        size_pol = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        size_pol.setControlType(QSizePolicy.Frame)
        size_pol.setHorizontalStretch(1)
        self.setSizePolicy(size_pol)

        def create_button(text, action):
            btn = QPushButton(text, self)
            btn.setStyleSheet("""
            QPushButton[selected="true"] {
                border: 2px inset grey;
                }""")
            btn.setFixedSize(QSize(60, 20))
            btn.pressed.connect(action)
            if not self.__buttons:
                self.set_button_selected(btn)
            self.__buttons.append(btn)
            layout.addWidget(btn)

        create_button("Move", self.action_move)
        create_button("Point", self.action_point)
        create_button("Line", self.action_line)
        create_button("Plane", self.action_plane)

        self.setFixedHeight(layout.sizeHint().height())
        layout.addStretch()

    def set_button_selected(self, btn):
        self.deselect_all_buttons()
        btn.setProperty("selected", "true")
        btn.style().unpolish(btn)
        btn.style().polish(btn)
        btn.update()

    def deselect_all_buttons(self):
        for btn in self.__buttons:
            btn.setProperty("selected", "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            btn.update()

    def action_move(self):
        self.set_button_selected(self.sender())
        EditorShared.get_gl_widget().move_object()

    def action_point(self):
        self.set_button_selected(self.sender())
        self.__editor().get_gl_widget().create_point()

    def action_line(self):
        self.set_button_selected(self.sender())
        self.__editor().get_gl_widget().create_line()

    def action_plane(self):
        self.set_button_selected(self.sender())
        self.__editor().get_gl_widget().create_plane()


class EditorGUI(QWidget, UpdateReceiverInterface):
    def __init__(self):
        super(EditorGUI, self).__init__()

        self.__action_splitter = QSplitter(Qt.Vertical)
        self.__main_splitter = QSplitter(Qt.Horizontal)

        self.__scene_exp = SceneExplorer(self)
        self.__gl_widget = GlScene(self, self.__scene_exp)
        self.__scene_act = SceneActions(self)

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

    def closeEvent(self, a0):
        self.__gl_widget.unload()


class GlScene(QGLWidget, GlSceneInterface):
    def __init__(self, editor, scene_explorer):
        super(GlScene, self).__init__(editor)
        self.__program = None
        self.__scene = Scene()
        self.__camera_controller = None
        self.__last_action = None
        self.__selected_objects = []
        self.__scene_explorer = ref(scene_explorer)

        size_pol = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        size_pol.setVerticalStretch(1)
        size_pol.setHorizontalStretch(1)
        size_pol.setControlType(QSizePolicy.Frame)
        self.setSizePolicy(size_pol)
        self.__geometry_builder = None

        self.installEventFilter(self)

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
        self.__scene.camera = Camera(self.width(), self.height())
        self.__camera_controller = CameraController(self.__scene.camera)
        SceneObject.default_shader_program = self.__program

        self.__scene.add_object(SceneGrid())
        self.__scene.add_object(SceneCoordAxis())

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
            case QEvent.Wheel:
                self.__camera_controller.handle_scroll(self, QWheelEvent(a1))
            case QEvent.MouseButtonPress:
                event = QMouseEvent(a1)
                if event.button() == Qt.LeftButton:
                    if not self.__geometry_builder:
                        self.try_select_scene_object(event)
                    else:
                        self.handle_geometry_builder(event)
                self.__camera_controller.handle_mouse_press(self, event)
            case QEvent.MouseButtonRelease:
                self.__camera_controller.handle_mouse_release(self, QMouseEvent(a1))
            case QEvent.MouseMove:
                self.__camera_controller.handle_mouse_move(self, QMouseEvent(a1))
        return super(QGLWidget, self).eventFilter(a0, a1)

    def unload(self):
        self.__scene.unload()
        self.__program.dispose()

    def no_action(self):
        self.__geometry_builder = None
        self.__last_action = self.no_action

    def move_object(self):
        self.__geometry_builder = None
        self.__last_action = self.move_object

    def create_point(self):
        self.__geometry_builder = PointBuilder(self.get_scene(), EditorShared.get_scene_explorer())
        self.__last_action = self.create_point

    def create_line(self):
        self.__geometry_builder = LineBuilder(self.get_scene(), EditorShared.get_scene_explorer())
        self.__last_action = self.create_line

    def create_plane(self):
        self.__geometry_builder = PlaneBuilder(self.get_scene(), EditorShared.get_scene_explorer())
        self.__last_action = self.create_plane

    def handle_move_object(self, event):
        # TODO:
        pass

    def handle_geometry_builder(self, event):
        pe = event.pos()
        pos = glm.vec2(pe.x(), pe.y())
        ready = self.__geometry_builder.on_click(pos)
        if ready:
            self.__geometry_builder = None
            self.__last_action()

        self.update()

    def try_select_scene_object(self, event: QMouseEvent) -> bool:
        x, y = event.x(), event.y()
        to_select = self.__scene.try_select_object(x, y)

        mods = event.modifiers()
        se = self.__scene_explorer()

        if not to_select or not Qt.ShiftModifier & mods:
            se.clear_selection()
        if to_select:
            to_select.selected = True
            se.set_scene_object_selected(to_select, True)

        self.update()
        return bool(to_select)


class SceneExplorer(QWidget, SceneExplorerInterface):
    def __init__(self, update_receiver: UpdateReceiverInterface):
        super(SceneExplorer, self).__init__()

        self.__update_receiver = ref(update_receiver)

        layout = QVBoxLayout()
        self.__list = SceneObjectList()

        self.__list.itemClicked.connect(self.update_property)
        self.__props = SceneObjectProperties()

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
        self.__list.add_scene_object(scene_object)

    def clear_selection(self):
        self.__list.deselect_all()

    def select_scene_object(self, scene_object, deselect_others=False):
        if deselect_others:
            self.__list.deselect_all()
        self.set_scene_object_selected(scene_object, True)

    def deselect_scene_object(self, scene_object: SceneObject):
        self.set_scene_object_selected(scene_object, False)

    def set_scene_object_selected(self, scene_object: SceneObject, value: bool):
        self.__list.set_scene_object_selected(scene_object, value)
        selected = self.__list.get_selected_items()
        if len(selected) == 1:
            self.update_property(selected[0])
        else:
            self.__props.clear()

    def update_property(self, item):
        widget = self.__list.itemWidget(item)
        self.__props.set_object(widget.get_object())
        self.__update_receiver().update()
        

class SceneObjectProperties(QWidget, SceneObjectPropertiesInterface):
    def __init__(self):
        super(SceneObjectProperties, self).__init__()
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.__so = None
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

    def clear(self):
        self.x_edit.setText("")
        self.y_edit.setText("")
        self.z_edit.setText("")
        self.__xyz.setDisabled(True)

    def set_scene_object(self, scene_object: SceneObject):
        self.__so = scene_object
        self.__xyz.setEnabled(True)
        self.update_properties()

    def update_properties(self):
        pos = self.__so.translation
        self.x_edit.setText(f'{pos.x:.4f}')
        self.y_edit.setText(f'{pos.y:.4f}')
        self.z_edit.setText(f'{pos.z:.4f}')

    def update_object(self):
        try:
            self.__so.set_position(float(self.x_edit.text()),
                                   float(self.y_edit.text()),
                                   float(self.z_edit.text()))
            EditorShared.get_gl_widget().update()
        except ValueError:
            self.update_props()


class PositionProperty(QWidget):
    def __init__(self, *args):
        super(PositionProperty, self).__init__(*args)


class SceneObjectList(QListWidget, SceneObjectListInterface):
    def __init__(self, ):
        self.__object_to_item = dict()
        super(SceneObjectList, self).__init__()

        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.itemSelectionChanged.connect(self.selection_changed_callback)
        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            kp = QKeyEvent(event)
            if kp.key() == Qt.Key_Delete:
                self.delete_selected()
                return True
        return super(SceneObjectList, self).eventFilter(obj, event)

    def delete_selected(self):
        for item in self.selectedItems():
            widget = self.itemWidget(item)
            obj = widget.get_object()
            EditorShared.get_scene().remove_object(obj)
            del self.__object_to_item[obj]
            self.removeItemWidget(item)
            self.takeItem(self.row(item))

    def deselect_all(self):
        for i in range(self.count()):
            item = self.item(i)
            widget = self.itemWidget(item)
            item.setSelected(False)
            widget.get_object().selected = False
        EditorShared.get_editor().update()

    def selection_changed_callback(self):
        for i in range(self.count()):
            item = self.item(i)
            widget = self.itemWidget(item)
            if widget is not None:
                widget.get_object().selected = item.isSelected()
        EditorShared.get_gl_widget().update()

    def add_scene_object(self, scene_object: SceneObject):
        item = QListWidgetItem()
        so_widget = SceneObjectWidget(scene_object)

        item.setSizeHint(so_widget.sizeHint())
        self.addItem(item)
        self.setItemWidget(item, so_widget)
        self.__object_to_item[so_widget.get_object()] = item

    def get_selected_items(self):
        selected = []
        for i in range(self.count()):
            item = self.item(i)
            if item.isSelected():
                selected.append(item)
        return selected

    def get_scene_object_item(self, scene_object: SceneObject):
        return self.__object_to_item[scene_object]

    def set_scene_object_selected(self, scene_object: SceneObject, value: bool):
        item = self.get_scene_object_item(scene_object)
        item.setSelected(value)
        widget = self.itemWidget(item)
        widget.get_object().selected = value

    def select_scene_object(self, scene_object: SceneObject,
                            deselect_others: bool = False):
        if deselect_others:
            self.deselect_all()
        self.set_scene_object_selected(scene_object, True)

