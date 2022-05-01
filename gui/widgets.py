from typing import Iterable
from weakref import ref

from PyQt5.QtCore import QSize, QEvent, Qt, QItemSelection
from PyQt5.QtGui import QKeyEvent, QFont
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QSizePolicy, QPushButton, \
    QListWidget, QAbstractItemView, \
    QListWidgetItem, QLabel, QShortcut

from gui.interfaces import SceneActionsInterface, GLSceneInterface
from scene.render_geometry import ScenePoint, SceneLine, ScenePlane
from scene.scene import Scene
from scene.scene_object import SceneObject


class SceneActions(QWidget, SceneActionsInterface):
    def __init__(self, gl_scene: GLSceneInterface):
        super(QWidget, self).__init__()

        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(layout)

        size_pol = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        size_pol.setControlType(QSizePolicy.Frame)
        size_pol.setHorizontalStretch(1)
        self.setSizePolicy(size_pol)

        self.__gl_scene = ref(gl_scene)
        self.__buttons = []

        def create_button(text, action, shortcut=None):
            btn = QPushButton(text, self)
            btn.setStyleSheet("""
            QPushButton[selected="true"] {
                border: 2px inset grey;
                }""")
            btn.setFixedSize(QSize(60, 20))
            btn.pressed.connect(action)
            if shortcut is not None:
                btn.setShortcut(shortcut)
                btn.setToolTip(shortcut)
            if not self.__buttons:
                self.__set_button_selected(btn)
            self.__buttons.append(btn)
            layout.addWidget(btn)

        create_button("Move", self.action_move, "M")
        create_button("Point", self.action_point, "P")
        create_button("Line", self.action_line, "L")
        create_button("Plane", self.action_plane, "Shift+P")
        create_button("Stress Test", self.action_stress_test)

        self.setFixedHeight(layout.sizeHint().height())
        layout.addStretch()

    def action_stress_test(self):
        self.__set_button_selected(self.sender())
        scene = self.__gl_scene().get_scene()
        from core.Base_geometry_objects import Point
        import glm
        for i in range(1000):
            scene.add_object(ScenePoint(Point(glm.vec3(glm.sin(i), glm.cos(i), glm.cos(-i)))))

    def __set_button_selected(self, btn):
        self.__deselect_all_buttons()
        btn.setProperty("selected", "true")
        btn.style().unpolish(btn)
        btn.style().polish(btn)
        btn.update()

    def __deselect_all_buttons(self):
        for btn in self.__buttons:
            btn.setProperty("selected", "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            btn.update()

    def action_move(self):
        self.__set_button_selected(self.sender())
        self.__gl_scene().move_object()

    def action_point(self):
        self.__set_button_selected(self.sender())
        self.__gl_scene().create_point()

    def action_line(self):
        self.__set_button_selected(self.sender())
        self.__gl_scene().create_line()

    def action_plane(self):
        self.__set_button_selected(self.sender())
        self.__gl_scene().create_plane()


class SceneObjectList(QListWidget):
    def __init__(self, gl_scene: GLSceneInterface):
        super(QListWidget, self).__init__()

        self.__gl_scene = ref(gl_scene)
        self.__object_to_item = {}
        self.__accepting_events = True
        self.__subscribe_to_scene(self.__gl_scene().get_scene())

        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.itemSelectionChanged.connect(self.__selection_changed)

    def __subscribe_to_scene(self, scene: Scene):
        scene.on_object_added += self.on_object_added
        scene.on_object_removed += self.on_object_removed
        scene.on_objects_selected += self.on_objects_selected
        scene.on_objects_deselected += self.on_objects_deselected

    def on_object_removed(self, scene_object: SceneObject):
        self.__accepting_events = False

        item = self.__object_to_item.pop(scene_object)
        self.removeItemWidget(item)
        self.takeItem(self.row(item))

        self.__accepting_events = True

    def on_object_added(self, scene_object: SceneObject):
        self.__accepting_events = False
        item = QListWidgetItem()
        so_widget = SceneObjectWidget(scene_object)

        item.setSizeHint(so_widget.sizeHint())
        self.addItem(item)
        self.setItemWidget(item, so_widget)
        self.__object_to_item[scene_object] = item
        self.__accepting_events = True

    def on_objects_selected(self, scene_objects: Iterable[SceneObject]):
        self.__accepting_events = False
        for obj in scene_objects:
            item = self.__object_to_item[obj]
            item.setSelected(True)

        self.__accepting_events = True

    def on_objects_deselected(self, scene_objects: Iterable[SceneObject]):
        self.__accepting_events = False
        for obj in scene_objects:
            item = self.__object_to_item[obj]
            item.setSelected(False)

        self.__accepting_events = True

    def __selection_changed(self):
        if not self.__accepting_events:
            return
        for i in range(self.count()):
            item = self.item(i)
            widget = self.itemWidget(item)
            if widget is not None:
                obj = widget.get_object()
                self.__set_object_selected(obj, item.isSelected())

        self.__gl_scene().update()

    def __set_object_selected(self, scene_object: SceneObject, value: bool):
        scene = self.__gl_scene().get_scene()
        if value:
            scene.select(scene_object)
        else:
            scene.deselect(scene_object)


class SceneObjectWidget(QWidget):
    __point_counter = 1
    __line_counter = 1
    __plane_counter = 1

    def __init__(self, scene_object: SceneObject):
        super(SceneObjectWidget, self).__init__()

        self.__scene_object = scene_object

        self.__layout = QHBoxLayout()

        font = QFont("Arial", 10)
        self.__name_label = QLabel()
        self.__name_label.setFont(font)

        if isinstance(scene_object, ScenePoint):
            text = f'Point{SceneObjectWidget.__point_counter}'
            SceneObjectWidget.__point_counter += 1
        elif isinstance(scene_object, SceneLine):
            text = f'Line{SceneObjectWidget.__line_counter}'
            SceneObjectWidget.__line_counter += 1
        elif isinstance(scene_object, ScenePlane):
            text = f'Plane{SceneObjectWidget.__plane_counter}'
            SceneObjectWidget.__plane_counter += 1
        else:
            text = 'Unknown'

        self.__name_label.setText(text)
        self.__layout.addWidget(self.__name_label)
        self.__layout.setContentsMargins(5, 2, 5, 2)
        self.setFixedHeight(20)

        self.__layout.addStretch()
        self.setLayout(self.__layout)

    def get_object(self):
        return self.__scene_object

    def sizeHint(self):
        return self.__layout.sizeHint()
