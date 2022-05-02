from abc import ABC
from typing import Optional
from weakref import ref

from PyQt5.QtCore import Qt

from core.event import Event
from core.interfaces import EventHandlerInterface
from scene.render_geometry import *
from scene.scene import Scene
from scene.scene_object import SceneObject
from core.Base_geometry_objects import *


class BaseBuilder(EventHandlerInterface, ABC):
    CLICK_DEPTH = 10

    def __init__(self, scene: Scene):
        self._has_any_progress = False
        self._scene = ref(scene)
        self.on_builder_ready = Event()
        self.on_builder_canceled = Event()
        self.__deselected = False

    def _deselect_all_once(self):
        if self.__deselected:
            return
        self._scene().deselect_all()
        self.__deselected = True

    def on_mouse_double_click(self, event: QMouseEvent):
        return self.on_mouse_pressed(event)

    @property
    def has_any_progress(self) -> bool:
        return self._has_any_progress

    def _push_object(self, scene_object: SceneObject, select: bool = False):
        self._scene().add_object(scene_object)
        if select:
            self._scene().select(scene_object)

    def _try_snap_to(self, screen_pos: glm.vec2) -> Optional[SceneObject]:
        return self._scene().find_selectable(screen_pos, SELECT_POINT, allow_selected=True)

    def cancel(self):
        self.on_builder_canceled.invoke()
        self._has_any_progress = False


class PointBuilder(BaseBuilder):
    def on_mouse_pressed(self, event: QMouseEvent):
        if event.button() != Qt.LeftButton:
            return False

        self._deselect_all_once()

        camera = self._scene().camera
        pos = extract_pos(event)
        ray = camera.screen_to_world(pos)

        place = camera.translation + BaseBuilder.CLICK_DEPTH * ray

        point = ScenePoint(Point(glm.vec3(place.x, place.y, place.z)))
        self._push_object(point, True)
        self.on_builder_ready.invoke()

        return True


class LineBuilder(BaseBuilder):
    def __init__(self, scene: Scene):
        super(LineBuilder, self).__init__(scene)
        self.p1 = None

    def on_mouse_pressed(self, event: QMouseEvent):
        if event.button() != Qt.LeftButton:
            return False

        self._deselect_all_once()
        self._has_any_progress = True

        camera = self._scene().camera
        pos = extract_pos(event)
        snap = self._try_snap_to(pos)

        if snap:
            if snap == self.p1:
                return False
            point = snap
            self._scene().select(point)
        else:
            ray = camera.screen_to_world(pos)
            place = camera.translation + BaseBuilder.CLICK_DEPTH * ray
            place = round_vec3(place)
            point = ScenePoint.from_pos(place)
            self._push_object(point, True)

        if self.p1:
            self.__line_from_points(self.p1, point)
            self.on_builder_ready.invoke()
        else:
            self.p1 = point

        return True

    def __line_from_points(self, p1, p2):
        child = SceneLine.common_child(p1, p2)
        if child is not None:
            self._scene().select(child)
            return child
        line = SceneLine.by_two_points(p1, p2)
        self._push_object(line, True)
        return line

    def cancel(self):
        self._has_any_progress = False
        scene = self._scene()
        if self.p1:
            scene.remove_object(self.p1)
        super(LineBuilder, self).cancel()


class PlaneBuilder(BaseBuilder):
    def __init__(self, scene: Scene):
        super(PlaneBuilder, self).__init__(scene)
        self.p1 = None
        self.p2 = None

    def on_mouse_pressed(self, event: QMouseEvent):
        if event.button() != Qt.LeftButton:
            return False

        self._deselect_all_once()
        self._has_any_progress = True

        camera = self._scene().camera
        pos = extract_pos(event)
        snap = self._try_snap_to(pos)

        if snap:
            if snap == self.p1 or snap == self.p2:
                return False
            point = snap
            self._scene().select(point)
        else:
            ray = camera.screen_to_world(pos)
            place = camera.translation + BaseBuilder.CLICK_DEPTH * ray
            place = round_vec3(place)
            point = ScenePoint.from_pos(place)
            self._push_object(point, True)

        if self.p2:
            self.__plane_from_points(self.p1, self.p2, point)
            self.on_builder_ready.invoke()
        elif self.p1:
            self.p2 = point
        else:
            self.p1 = point

        return True

    def __plane_from_points(self, p1, p2, p3):
        child = ScenePlane.common_child(p1, p2, p3)
        if child is not None:
            self._scene().select(child)
            return child
        plane = ScenePlane.by_three_points(p1, p2, p3)
        self._push_object(plane, True)
        return plane

    def cancel(self):
        scene = self._scene()
        if self.p1:
            scene.remove_object(self.p1)
        if self.p2:
            scene.remove_object(self.p2)
        super(PlaneBuilder, self).cancel()


class EdgeBuilder(BaseBuilder):
    def __init__(self, scene: Scene):
        super(EdgeBuilder, self).__init__(scene)
        self.p1 = None

    def on_mouse_pressed(self, event: QMouseEvent):
        if event.button() != Qt.LeftButton:
            return False

        self._deselect_all_once()
        self._has_any_progress = True

        camera = self._scene().camera
        pos = extract_pos(event)
        snap = self._try_snap_to(pos)

        if snap:
            if snap == self.p1:
                return False
            point = snap
            self._scene().select(point)
        else:
            ray = camera.screen_to_world(pos)
            place = camera.translation + BaseBuilder.CLICK_DEPTH * ray
            place = round_vec3(place)
            point = ScenePoint.from_pos(place)
            self._push_object(point, True)

        if self.p1:
            self.__edge_from_points(self.p1, point)

            shift = event.modifiers() & Qt.ShiftModifier
            if shift:
                self.p1 = point
                self._has_any_progress = False
            else:
                self.on_builder_ready.invoke()
        else:
            self.p1 = point

        return True

    def __edge_from_points(self, p1, p2):
        child = SceneEdge.common_child(p1, p2)
        if child is not None:
            self._scene().select(child)
            return child
        edge = SceneEdge.by_two_points(p1, p2)
        self._push_object(edge, True)
        return edge

    def cancel(self):
        scene = self._scene()
        if self._has_any_progress:
            scene.remove_object(self.p1)
        super(EdgeBuilder, self).cancel()


class FaceBuilder(BaseBuilder):
    def __init__(self, scene: Scene):
        super(FaceBuilder, self).__init__(scene)
        self.p1 = None
        self.p2 = None
        self.edge = None

    def on_mouse_pressed(self, event: QMouseEvent):
        if event.button() != Qt.LeftButton:
            return False

        self._deselect_all_once()
        self._has_any_progress = True

        camera = self._scene().camera
        pos = extract_pos(event)
        snap = self._try_snap_to(pos)

        if snap:
            if snap == self.p1 or snap == self.p2:
                return False
            point = snap
            self._scene().select(point)
        else:
            ray = camera.screen_to_world(pos)
            place = camera.translation + BaseBuilder.CLICK_DEPTH * ray
            place = round_vec3(place)
            point = ScenePoint.from_pos(place)
            self._push_object(point, True)

        if self.p2:
            edge2 = self.__edge_from_points(self.p2, point)
            edge3 = self.__edge_from_points(point, self.p1)
            face = self.__face_from_points(self.p1, self.p2, point)
            face.add_parents(self.edge, edge2, edge3)

            shift = event.modifiers() & Qt.ShiftModifier
            if shift:
                self.edge = edge3
                self.p2 = point
                self._has_any_progress = False
            else:
                self.on_builder_ready.invoke()
        elif self.p1:
            self.p2 = point
            self.edge = self.__edge_from_points(self.p1, self.p2)
        else:
            self.p1 = point

        return True

    def __edge_from_points(self, p1, p2):
        child = SceneEdge.common_child(p1, p2)
        if child is not None:
            self._scene().select(child)
            return child
        edge = SceneEdge.by_two_points(p1, p2)
        self._push_object(edge, True)
        return edge

    def __face_from_points(self, p1, p2, p3):
        child = SceneFace.common_child(p1, p2, p3)
        if child is not None:
            self._scene().select(child)
            return child
        face = SceneFace.by_three_points(p1, p2, p3)
        self._push_object(face, True)
        return face

    def cancel(self):
        scene = self._scene()
        if self._has_any_progress:
            if self.p1 is not None:
                scene.remove_object(self.p1)
            if self.p2 is not None:
                scene.remove_object(self.p2)
            if self.edge is not None:
                scene.remove_object(self.edge)
        return super(FaceBuilder, self).cancel()
