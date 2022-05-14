from typing import Iterable
from weakref import ref

from PyQt5.QtCore import QSize, QItemSelection
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QSizePolicy, QPushButton,
                             QListWidget, QAbstractItemView,
                             QListWidgetItem, QLabel)

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
        create_button("Edge", self.action_edge, "E")
        create_button("Face", self.action_face, "F")
        layout.addStretch()
        create_button("Line", self.action_line, "L")
        create_button("Plane", self.action_plane, "Shift+P")
        layout.addStretch()
        create_button("Rect", self.action_rect, "Shift+R")
        layout.addStretch()
        create_button("Stress", self.action_stress_test)

        self.setFixedHeight(layout.sizeHint().height())

    def action_rect(self):
        self.__set_button_selected(self.sender())
        self.__gl_scene().create_rect()

    def action_stress_test(self):
        scene = self.__gl_scene().get_scene()

        from core.Base_geometry_objects import Point
        import glm
        import random

        offset = glm.vec3(random.random(), random.random(), random.random())
        start = random.random() * 100
        for i in range(1000):
            angle = i + start
            pos = glm.vec3(glm.sin(angle), glm.cos(angle), glm.cos(angle) * glm.sin(angle))
            scene.add_object(ScenePoint(Point(pos + offset)))

        self.__gl_scene().redraw()

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

    def action_edge(self):
        self.__set_button_selected(self.sender())
        self.__gl_scene().create_edge()

    def action_face(self):
        self.__set_button_selected(self.sender())
        self.__gl_scene().create_face()

    def action_plane(self):
        self.__set_button_selected(self.sender())
        self.__gl_scene().create_plane()


class SceneObjectList(QListWidget):
    def __init__(self, gl_scene: GLSceneInterface):
        super(QListWidget, self).__init__()

        self.__gl_scene = ref(gl_scene)
        self.__object_to_item = {}
        self.__item_to_object = {}
        self.__subscribe_to_scene(self.__gl_scene().get_scene())

        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.selectionModel().selectionChanged.connect(self.__selection_changed)

    def __subscribe_to_scene(self, scene: Scene):
        scene.on_objects_added += self.on_objects_added
        scene.on_objects_removed += self.on_objects_removed
        scene.on_objects_selected += self.on_objects_selected
        scene.on_objects_deselected += self.on_objects_deselected

    def on_objects_removed(self, scene_objects: Iterable[SceneObject]):
        self.__begin_update()
        for scene_object in scene_objects:
            item = self.__object_to_item.pop(scene_object)
            self.__item_to_object.pop(item)
            self.takeItem(self.row(item))
        self.__end_update()

    def on_objects_added(self, scene_objects: Iterable[SceneObject]):
        self.__begin_update()
        for scene_object in scene_objects:
            item = SceneObjectItem(scene_object)
            self.addItem(item)
            self.__object_to_item[scene_object] = item
            self.__item_to_object[item] = scene_object
        self.__end_update()

    def on_objects_selected(self, scene_objects: Iterable[SceneObject]):
        self.__begin_update()
        for obj in scene_objects:
            item = self.__object_to_item[obj]
            item.setSelected(True)
        self.__end_update()

    def on_objects_deselected(self, scene_objects: Iterable[SceneObject]):
        self.__begin_update()
        for obj in scene_objects:
            item = self.__object_to_item[obj]
            item.setSelected(False)
        self.__end_update()

    def __begin_update(self):
        self.setUpdatesEnabled(False)
        self.blockSignals(True)

    def __end_update(self):
        self.setUpdatesEnabled(True)
        self.blockSignals(False)
        self.update()

    def __selection_changed(self, selected: QItemSelection, deselected: QItemSelection):
        for value, selection in [(True, selected), (False, deselected)]:
            for sel_range in selection:
                for index in sel_range.indexes():
                    row = index.row()
                    item = self.item(row)
                    obj = self.__item_to_object[item]
                    self.__set_object_selected(obj, value)

        self.__gl_scene().redraw()

    def __set_object_selected(self, scene_object: SceneObject, value: bool):
        scene = self.__gl_scene().get_scene()
        if value:
            scene.select(scene_object)
        else:
            scene.deselect(scene_object)


class SceneObjectItem(QListWidgetItem):
    def __init__(self, scene_object: SceneObject):
        super(SceneObjectItem, self).__init__()

        scene_object.on_updated += self.__object_updated

        self.__scene_object = scene_object

        font = QFont("Arial", 10)
        self.setText(scene_object.name)
        self.setFont(font)

    def __object_updated(self, obj):
        self.setText(obj.name)

    def get_object(self):
        return self.__scene_object

    def __hash__(self):
        return hash(self.__scene_object)
