from typing import Iterable
from weakref import ref

import glm
import random

import numpy as np
from PyQt5.QtCore import QSize, QItemSelection
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QSizePolicy, QPushButton,
                             QListWidget, QAbstractItemView,
                             QListWidgetItem, QListView, QShortcut)

import profiling.profiler
from gui.interfaces import SceneActionsInterface, GLSceneInterface
from scene.render_geometry import ScenePoint, SceneEdge
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
        create_button("Point", self.action_point, "Alt+P")
        create_button("Edge", self.action_edge, "Alt+E")
        create_button("Face", self.action_face, "Alt+F")
        create_button("Divide", self.action_divide, "Alt+D")
        layout.addStretch()
        create_button("Line", self.action_line, "Alt+L")
        create_button("Plane", self.action_plane, "Alt+Shift+P")
        layout.addStretch()
        create_button("Rect", self.action_rect, "Alt+Shift+R")
        layout.addStretch()
        create_button("Stress", self.action_stress_test1)
        create_button("Space", self.action_stress_test2)

        def create_shortcut(key, action):
            sc = QShortcut(key, self)
            sc.activated.connect(action)

        create_shortcut("W", self.action_w)
        create_shortcut("S", self.action_s)
        create_shortcut("A", self.action_a)
        create_shortcut("D", self.action_d)
        create_shortcut("Q", self.action_q)
        create_shortcut("E", self.action_e)

        self.setFixedHeight(layout.sizeHint().height())

    def action_w(self):
        move = glm.vec3(0, 0, 1)
        self.__gl_scene().move(move)

    def action_s(self):
        move = glm.vec3(0, 0, -1)
        self.__gl_scene().move(move)

    def action_a(self):
        move = glm.vec3(1, 0, 0)
        self.__gl_scene().move(move)

    def action_d(self):
        move = glm.vec3(-1, 0, 0)
        self.__gl_scene().move(move)

    def action_q(self):
        move = glm.vec3(0, 1, 0)
        self.__gl_scene().move(move)

    def action_e(self):
        move = glm.vec3(0, -1, 0)
        self.__gl_scene().move(move)

    def action_divide(self):
        self.__set_button_selected(self.sender())
        self.__gl_scene().create_division()

    def action_rect(self):
        self.__set_button_selected(self.sender())
        self.__gl_scene().create_rect()

    def action_stress_test2(self):
        scene = self.__gl_scene().get_scene()
        iter_count = 1_000_000
        pos_range = 1000
        points = []
        for i in range(iter_count):
            pos = glm.vec3(random.randint(-pos_range, pos_range),
                           random.randint(-pos_range, pos_range),
                           random.randint(-pos_range, pos_range))
            point = ScenePoint.by_pos(pos)
            points.append(point)
        scene.add_objects(points)

        self.__gl_scene().redraw()

    def action_stress_test1(self):
        scene = self.__gl_scene().get_scene()

        offset_range = 100
        offset = glm.vec3(random.randint(-offset_range, offset_range),
                          random.randint(-offset_range, offset_range),
                          random.randint(-offset_range, offset_range))

        def set1(angle):
            return glm.vec3(glm.sin(angle * 5), glm.tan(angle),
                            (glm.sin(angle) + glm.cos(angle)) ** 3)

        def set2(angle):
            return glm.vec3(glm.cos(angle), glm.atan(angle),
                            glm.sin(angle) * glm.cos(angle))

        def set3(angle):
            return glm.vec3(glm.cos(angle / 2) * glm.tanh(angle),
                            glm.cos(angle), glm.sin(angle) ** 3)

        def set4(angle):
            return glm.vec3(glm.tanh(angle) ** 2, glm.sin(glm.cot(angle)),
                            glm.cos(angle) * glm.cos(angle * 2))

        def set5(angle):
            return glm.vec3(glm.sqrt(glm.tan(angle)), glm.cos(angle / 3) ** 5,
                            glm.cos(angle) * glm.acoth(angle * 2))

        func = random.choice([set1, set2, set3, set4, set5])
        size = random.randint(15, 30)

        prev = None

        objs = []

        iter_count = 1024
        for i in range(iter_count):
            angle = i / (glm.pi() / 2)
            pos = func(angle) * size
            if np.isnan(pos.x) or np.isnan(pos.y) or np.isnan(pos.z):
                continue

            point = ScenePoint.by_pos(pos + offset)
            objs.append(point)
            if prev is not None:
                edge = SceneEdge.by_two_points(prev, point)
                objs.append(edge)
            prev = point

        scene.add_objects(objs)
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

        gl_scene.on_scene_changed += self.__on_scene_changed

        self.__gl_scene = ref(gl_scene)
        self.__object_to_item = {}
        self.__item_to_object = {}

        self.setUniformItemSizes(True)
        self.setLayoutMode(QListView.Batched)
        self.setBatchSize(256)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.selectionModel().selectionChanged.connect(self.__selection_changed)

    def __on_scene_changed(self, previous_scene, new_scene):
        self.blockSignals(True)
        self.setUpdatesEnabled(False)
        self.clear()
        self.blockSignals(False)
        self.setUpdatesEnabled(True)
        if previous_scene is not None:
            previous_scene.on_objects_added -= self.on_objects_added
            previous_scene.on_objects_removed -= self.on_objects_removed
            previous_scene.on_objects_selected -= self.on_objects_selected
            previous_scene.on_objects_deselected -= self.on_objects_deselected
        if new_scene is not None:
            new_scene.on_objects_added += self.on_objects_added
            new_scene.on_objects_removed += self.on_objects_removed
            new_scene.on_objects_selected += self.on_objects_selected
            new_scene.on_objects_deselected += self.on_objects_deselected

    @profiling.profiler.profile
    def on_objects_removed(self, scene_objects: Iterable[SceneObject]):
        self.__begin_update()
        for obj in scene_objects:
            self.__remove_object(obj)
        self.__end_update()

    @profiling.profiler.profile
    def __remove_object(self, scene_object):
        item = self.__object_to_item.pop(scene_object)
        self.__item_to_object.pop(item)
        self.takeItem(self.row(item))

    @profiling.profiler.profile
    def on_objects_added(self, scene_objects: Iterable[SceneObject]):
        self.__begin_update()
        for scene_object in scene_objects:
            item = SceneObjectItem(scene_object)
            self.addItem(item)
            self.__object_to_item[scene_object] = item
            self.__item_to_object[item] = scene_object
        self.__end_update()

    @profiling.profiler.profile
    def on_objects_selected(self, scene_objects: Iterable[SceneObject]):
        self.__begin_update()
        for obj in scene_objects:
            item = self.__object_to_item[obj]
            item.setSelected(True)
        self.__end_update()

    @profiling.profiler.profile
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

    def __selection_changed(self, selected: QItemSelection,
                            deselected: QItemSelection):
        scene = self.__gl_scene().get_scene()

        scene.on_objects_selected -= self.on_objects_selected
        scene.on_objects_deselected -= self.on_objects_deselected

        for value, selection in [(True, selected), (False, deselected)]:
            for sel_range in selection:
                for index in sel_range.indexes():
                    row = index.row()
                    item = self.item(row)
                    obj = self.__item_to_object.get(item, None)
                    if obj is None:
                        continue
                    self.__set_object_selected(obj, value)

        scene.on_objects_selected += self.on_objects_selected
        scene.on_objects_deselected += self.on_objects_deselected
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
