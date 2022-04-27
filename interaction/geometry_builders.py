from abc import ABC
from weakref import ref

from PyQt5.QtCore import Qt

from core.event import Event
from core.interfaces import EventHandlerInterface
from scene.render_geometry import *
from scene.scene import Scene
from scene.scene_object import SceneObject
from core.geometry import *


class BaseBuilder(EventHandlerInterface, ABC):
    CLICK_DEPTH = 10

    def __init__(self, scene: Scene):
        self._scene = ref(scene)
        self.on_builder_ready = Event()
        self.on_builder_canceled = Event()

    def _push_object(self, scene_object: SceneObject, select: bool = False):
        self._scene().add_object(scene_object)
        if select:
            self._scene().select(scene_object)

    def _try_snap_to(self, screen_pos: glm.vec2):
        return self._scene().find_selectable(screen_pos, SELECT_POINT)


class PointBuilder(BaseBuilder):
    def __init__(self, scene: Scene):
        super().__init__(scene)
        scene.deselect(list(filter(lambda x: x.selected, scene.objects)))

    def on_mouse_pressed(self, event: QMouseEvent):
        if event.button() != Qt.LeftButton:
            return

        camera = self._scene().camera
        pos = extract_pos(event)
        ray = camera.screen_to_world(pos)

        place = camera.translation + BaseBuilder.CLICK_DEPTH * ray

        point = ScenePoint(Point(place.x, place.y, place.z))
        self._push_object(point, True)


class LineBuilder(BaseBuilder):
    def __init__(self, scene: Scene):
        super(LineBuilder, self).__init__(scene)
        self.p1 = None
        scene.deselect(list(filter(lambda x: x.selected, scene.objects)))

    def on_mouse_pressed(self, event: QMouseEvent):
        if event.button() != Qt.LeftButton:
            return

        camera = self._scene().camera
        pos = extract_pos(event)
        snap = self._try_snap_to(pos)

        if snap:
            if snap == self.p1:
                return
            point = snap
        else:
            ray = camera.screen_to_world(pos)
            place = camera.translation + BaseBuilder.CLICK_DEPTH * ray
            point = ScenePoint(Point(place.x, place.y, place.z))
            self._push_object(point, True)

        if self.p1:
            line = SceneLine(LineBy2Points(self.p1.point, point.point))
            self._push_object(line, True)
            self.on_builder_ready.invoke()
        else:
            self.p1 = point


class PlaneBuilder(BaseBuilder):
    def __init__(self, scene: Scene):
        super(PlaneBuilder, self).__init__(scene)
        self.p1 = None
        self.p2 = None
        scene.deselect(list(filter(lambda x: x.selected, scene.objects)))

    def on_mouse_pressed(self, event: QMouseEvent):
        if event.button() != Qt.LeftButton:
            return

        camera = self._scene().camera
        pos = extract_pos(event)
        snap = self._try_snap_to(pos)

        if snap:
            if snap == self.p1 or snap == self.p2:
                return
            point = snap
        else:
            ray = camera.screen_to_world(pos)
            place = camera.translation + BaseBuilder.CLICK_DEPTH * ray
            point = ScenePoint(Point(place.x, place.y, place.z))
            self._push_object(point)

        if self.p2:
            plane = ScenePlane(PlaneBy3Points(self.p1.point, self.p2.point, point.point))
            self._push_object(plane)
            self._scene().select(plane)

            self.on_builder_ready.invoke()
        elif self.p1:
            self._scene().select(point)
            self.p2 = point
        else:
            self._scene().select(point)
            self.p1 = point
