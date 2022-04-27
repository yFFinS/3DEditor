from weakref import ref

from PyQt5.QtCore import QSize, QEvent, Qt
from PyQt5.QtGui import QKeyEvent, QFont
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QSizePolicy, QPushButton, QListWidget, QAbstractItemView, \
    QListWidgetItem, QLabel

from gui.interfaces import SceneActionsInterface, GLSceneInterface
from scene.interfaces import SceneEventListener
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

        def create_button(text, action):
            btn = QPushButton(text, self)
            btn.setStyleSheet("""
            QPushButton[selected="true"] {
                border: 2px inset grey;
                }""")
            btn.setFixedSize(QSize(60, 20))
            btn.pressed.connect(action)
            if not self.__buttons:
                self.__set_button_selected(btn)
            self.__buttons.append(btn)
            layout.addWidget(btn)

        create_button("Move", self.action_move)
        create_button("Point", self.action_point)
        create_button("Line", self.action_line)
        create_button("Plane", self.action_plane)

        self.setFixedHeight(layout.sizeHint().height())
        layout.addStretch()

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


class SceneObjectList(QListWidget, SceneEventListener):
    def __init__(self, gl_scene: GLSceneInterface):
        super(QListWidget, self).__init__()

        self.__gl_scene = ref(gl_scene)
        self.__object_to_item = {}
        self.__accepting_events = True
        self.__subscribe_to_scene(self.__gl_scene().get_scene())

        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.itemSelectionChanged.connect(self.__selection_changed)
        self.installEventFilter(self)

    def __subscribe_to_scene(self, scene: Scene):
        scene.on_object_added += self.on_object_added
        scene.on_object_removed += self.on_object_removed
        scene.on_objects_selected += self.on_objects_selected
        scene.on_objects_deselected += self.on_objects_deselected

    def on_object_removed(self, scene_object: SceneObject):
        item = self.__object_to_item.pop(scene_object)
        self.removeItemWidget(item)
        self.takeItem(self.row(item))

    def on_object_added(self, scene_object: SceneObject):
        item = QListWidgetItem()
        so_widget = SceneObjectWidget(scene_object)

        item.setSizeHint(so_widget.sizeHint())
        self.addItem(item)
        self.setItemWidget(item, so_widget)
        self.__object_to_item[scene_object] = item

    def on_objects_selected(self, scene_objects: list[SceneObject]):
        self.__accepting_events = False
        for obj in scene_objects:
            item = self.__object_to_item[obj]
            item.setSelected(True)

        self.__accepting_events = True

    def on_objects_deselected(self, scene_objects: list[SceneObject]):
        self.__accepting_events = False
        for obj in scene_objects:
            item = self.__object_to_item[obj]
            item.setSelected(False)

        self.__accepting_events = True

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            kp = QKeyEvent(event)
            if kp.key() == Qt.Key_Delete:
                self.__delete_selected()
                return True

        return super(QListWidget, self).eventFilter(obj, event)

    def __delete_selected(self):
        scene = self.__gl_scene().get_scene()
        for item in self.selectedItems():
            obj = self.itemWidget(item).get_object()
            scene.remove_object(obj)

    def __deselect_all(self):
        scene = self.__gl_scene().get_scene()
        scene.deselect(list(self.__object_to_item.keys()))

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

    def get_selected_items(self):
        selected = []
        for i in range(self.count()):
            item = self.item(i)
            if item.isSelected():
                selected.append(item)
        return selected

    def __set_object_selected(self, scene_object: SceneObject, value: bool):
        scene = self.__gl_scene().get_scene()
        if value:
            scene.select(scene_object)
        else:
            scene.deselect(scene_object)

    def select_scene_object(self, scene_object: SceneObject,
                            deselect_others: bool = False):
        if deselect_others:
            self.__deselect_all()
        self.__set_object_selected(scene_object, True)


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
