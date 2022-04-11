from PyQt5.QtCore import QSize, QEvent, QObject, Qt
from PyQt5.QtGui import QFont, QPalette, QKeyEvent, QMouseEvent, QWheelEvent
from PyQt5.QtWidgets import (QVBoxLayout, QListWidgetItem, QLineEdit,
                             QHBoxLayout, QWidget, QLabel, QMainWindow,
                             QAction, QListWidget, QAbstractItemView)
from PyQt5.QtOpenGL import QGLWidget

from scene import *
from render_geometry import *
from shared import EditorShared
from camera import Camera, CameraController


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(500, 300, 1000, 600)

        EditorShared.init(EditorGUI())

        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('Файл')
        sceneMenu = menuBar.addMenu('Сцена')

        createPointAction = QAction("Создать точку", self)
        createPointAction.triggered.connect(self.editor.create_point)
        sceneMenu.addAction(createPointAction)
        self.setCentralWidget(self.editor)
        self.setWindowTitle('3D Editor')

    @property
    def editor(self):
        return EditorShared.get_editor()

    def closeEvent(self, a0):
        self.editor.closeEvent(a0)


class EditorGUI(QWidget):
    def __init__(self):
        super(EditorGUI, self).__init__()

        self.__gl_widget = GlSceneWidget(self)
        self.__scene_exp = SceneExplorer(self)

        self.__mainLayout = QHBoxLayout()

        self.__mainLayout.addWidget(self.__scene_exp)
        self.__mainLayout.addWidget(self.__gl_widget)

        self.setLayout(self.__mainLayout)

    def get_scene_explorer(self):
        return self.__scene_exp

    def get_scene(self):
        return self.__gl_widget.get_scene()

    def get_gl_widget(self):
        return self.__gl_widget

    def create_point(self, x, y, z):
        scene = self.get_scene()
        scene_exp = self.get_scene_explorer()
        obj = ScenePoint(Point(x, y, z))
        scene.add_object(obj)
        widget = SceneObjectWidget(obj)
        scene_exp.add_scene_object_widget(widget)

        self.get_gl_widget().update()

    def closeEvent(self, a0):
        self.__gl_widget.unload()


class GlSceneWidget(QGLWidget):
    def __init__(self, parent=None):
        super(GlSceneWidget, self).__init__(parent)
        self.__program = None
        self.__scene = Scene()
        self.__camera_controller = None
        self.__selected_objects = []

        self.installEventFilter(self)

    def get_scene(self):
        return self.__scene

    def sizeHint(self):
        return QSize(800, 640)

    def initializeGL(self):
        GL.glClearColor(144 / 256, 144 / 256, 144 / 256, 1)
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        GL.glPointSize(4)
        GL.glLineWidth(1)
        GL.glEnable(GL.GL_LINE_SMOOTH)

        self.__program = ShaderProgram("shaders/default.vert", "shaders/default.frag")
        self.__scene.camera = Camera(self.width(), self.height())
        self.__camera_controller = CameraController(self.__scene.camera)
        SceneObject.default_shader_program = self.__program

        self.__scene.add_object(SceneCoordAxisX())
        self.__scene.add_object(SceneCoordAxisY())
        self.__scene.add_object(SceneCoordAxisZ())

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
                    self.try_select_scene_object(event)
                self.__camera_controller.handle_mouse_press(self, event)
            case QEvent.MouseButtonRelease:
                self.__camera_controller.handle_mouse_release(self, QMouseEvent(a1))
            case QEvent.MouseMove:
                self.__camera_controller.handle_mouse_move(self, QMouseEvent(a1))
        return super(QGLWidget, self).eventFilter(a0, a1)

    def unload(self):
        self.__scene.unload()
        self.__program.dispose()

    def try_select_scene_object(self, event):
        to_select = None
        select_w = -1

        x, y = event.x(), event.y()
        camera = self.__scene.camera
        for obj in self.__scene.get_objects():
            if obj in self.__selected_objects:
                continue
            weight = obj.get_selection_weight(camera, x, camera.height - y)
            if weight is None:
                continue
            if weight < 0 or weight > 1:
                raise ValueError(f"Вес должен быть от 0 до 1. Был {weight}.")
            if weight > select_w:
                select_w = weight
                to_select = obj

        mods = event.modifiers()
        se = EditorShared.get_scene_explorer()

        if not to_select or not Qt.ShiftModifier & mods:
            se.clear_selection()
            self.__selected_objects.clear()
        if to_select:
            self.__selected_objects.append(to_select)
            to_select.selected = True
            se.set_scene_object_selected(to_select, True)

        self.update()


class SceneExplorer(QWidget):
    def __init__(self, *args):
        super(SceneExplorer, self).__init__(*args)

        self.__mainLayout = QVBoxLayout()
        self.__list = SceneObjectList(self)

        self.__list.setFixedHeight(300)
        self.__list.setFixedWidth(300)
        self.__list.itemClicked.connect(self.update_property)
        self.__props = SceneObjectProperties()
        self.__props.setFixedWidth(300)

        self.__mainLayout.addWidget(self.__list)
        self.__mainLayout.addWidget(self.__props)

        self.setLayout(self.__mainLayout)

    def add_scene_object_widget(self, so_widget):
        self.__list.add_scene_object_widget(so_widget)

    def clear_selection(self):
        self.__list.deselect_all()

    def set_scene_object_selected(self, scene_object, value):
        self.__list.set_scene_object_selected(scene_object, value)

    def update_property(self, item):
        widget = self.__list.itemWidget(item)
        self.__props.set_object(widget.get_object())
        

class SceneObjectProperties(QWidget):
    def __init__(self, *args):
        super(SceneObjectProperties, self).__init__(*args)
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.__so = None
        self.__xyz = QWidget(self)
        xyz_layout = QHBoxLayout()
        self.x_edit = QLineEdit(self)
        self.y_edit = QLineEdit(self)
        self.z_edit = QLineEdit(self)
        self.x_edit.textChanged.connect(self.update_object)
        self.y_edit.textChanged.connect(self.update_object)
        self.z_edit.textChanged.connect(self.update_object)

        xyz_layout.addWidget(self.x_edit)
        xyz_layout.addWidget(self.y_edit)
        xyz_layout.addWidget(self.z_edit)
        self.__xyz.setLayout(xyz_layout)
        layout.addWidget(self.__xyz)

    def set_object(self, scene_object):
        self.__so = scene_object
        self.update_props()

    def update_props(self):
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


class SceneObjectList(QListWidget):
    def __init__(self, *args):
        self.__object_to_item = dict()
        super(SceneObjectList, self).__init__(*args)

        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.itemSelectionChanged.connect(self.selection_changed_callback)

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
            widget.get_object().selected = item.isSelected()
        EditorShared.get_editor().update()

    def add_scene_object_widget(self, so_widget):
        item = QListWidgetItem()
        item.setSizeHint(so_widget.sizeHint())
        self.addItem(item)
        self.setItemWidget(item, so_widget)
        self.__object_to_item[so_widget.get_object()] = item

    def set_scene_object_selected(self, scene_object, value):
        item = self.__object_to_item[scene_object]
        item.setSelected(value)
        widget = self.itemWidget(item)
        widget.get_object().selected = value


class SceneObjectWidget(QWidget):
    __point_counter = 1
    __line_counter = 1

    def __init__(self, scene_object):
        super(SceneObjectWidget, self).__init__()
        self.__layout = QHBoxLayout()

        font = QFont("Arial", 14)
        self.__name_label = QLabel(self)
        self.__name_label.setFont(font)

        if isinstance(scene_object, ScenePoint):
            text = f'Point{SceneObjectWidget.__point_counter}'
            SceneObjectWidget.__point_counter += 1
        elif isinstance(scene_object, SceneLine):
            text = f'Line{SceneObjectWidget.__line_counter}'
            SceneObjectWidget.__line_counter += 1
        else:
            text = 'Unknown'

        self.__name_label.setText(text)
        self.__layout.addWidget(self.__name_label)
        self.__scene_object = scene_object

        self.__layout.addStretch()
        self.setLayout(self.__layout)

    def get_object(self):
        return self.__scene_object

    def sizeHint(self):
        return self.__layout.sizeHint()

