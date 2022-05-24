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
        self._ready = False
        self._scene = ref(scene)
        self.on_builder_ready = Event()
        self.on_builder_canceled = Event()
        self.__deselected = False

    def _deselect_all_once(self):
        if self.__deselected:
            return
        self._deselect_all()

    def _deselect_all(self):
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

    def _try_snap_to(self, screen_pos: glm.vec2, mask: int = SELECT_POINT) \
            -> Optional[SceneObject]:
        return self._scene().find_selectable(screen_pos, mask,
                                             allow_selected=True)

    def _set_ready(self):
        self._ready = True
        self.__deselected = False
        self._has_any_progress = False
        self.on_builder_ready.invoke()

    def _reset_ready(self):
        self._ready = False

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

        self._set_ready()

        return True


class LineBuilder(BaseBuilder):
    def __init__(self, scene: Scene):
        super(LineBuilder, self).__init__(scene)
        self.p1 = None

    def on_mouse_pressed(self, event: QMouseEvent):
        if event.button() != Qt.LeftButton:
            return False

        if self._ready:
            self.p1 = None

        self._reset_ready()
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
            point = ScenePoint.by_pos(place)
            self._push_object(point, True)

        if self.p1:
            self.__line_from_points(self.p1, point)
            self._set_ready()
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
        if not self._ready and self.p1:
            scene.remove_object(self.p1)
        super(LineBuilder, self).cancel()


class PlaneBuilder(BaseBuilder):
    def __init__(self, scene: Scene):
        super(PlaneBuilder, self).__init__(scene)
        self.points = []
        self.plane = None
        self.line = None
        self.segment = None

    def on_mouse_pressed(self, event: QMouseEvent):
        if event.button() != Qt.LeftButton:
            return False

        self._reset_ready()
        self._deselect_all_once()
        self._has_any_progress = True

        camera = self._scene().camera
        pos = extract_pos(event)

        mask = SELECT_POINT
        if len(self.points) < 2:
            mask |= SELECT_PLANE | SELECT_EDGE | SELECT_LINE
        snap = self._try_snap_to(pos, mask=mask)

        if snap:
            if snap in self.points or snap == self.plane or snap == self.line or snap == self.segment:
                return False
            if isinstance(snap, ScenePlane):
                if self.plane is not None:
                    self._scene().deselect(self.plane)
                self.plane = snap
            elif isinstance(snap, SceneLine):
                if self.line is not None:
                    self._scene().deselect(self.line)
                self.line = snap
            elif isinstance(snap, SceneEdge):
                if self.segment is not None:
                    self._scene().deselect(self.segment)
                self.segment = snap
            else:
                self.points.append(snap)
            self._scene().select(snap)
        else:
            ray = camera.screen_to_world(pos)
            place = camera.translation + BaseBuilder.CLICK_DEPTH * ray
            place = round_vec3(place)
            point = ScenePoint.by_pos(place)
            self._push_object(point, True)
            self.points.append(point)

        plane = None
        if len(self.points) == 1:
            if self.plane:
                plane = self.__plane_from_point_and_plane(self.points[0],
                                                          self.plane)
            elif self.line:
                plane = self.__plane_from_point_and_line(self.points[0],
                                                         self.line)
            elif self.segment:
                plane = self.__plane_from_point_and_segment(self.points[0],
                                                            self.segment)
        elif len(self.points) == 3:
            plane = self.__plane_from_points(*self.points)

        if plane:
            self._set_ready()
            self.points.clear()
            self.plane = None
            self.line = None
            self.segment = None

        return True

    def __plane_from_point_and_plane(self, point, plane):
        child = ScenePlane.common_child(point, plane)
        if child is not None:
            self._scene().select(child)
            return child
        plane = ScenePlane.by_point_and_plane(point, plane)
        self._push_object(plane, True)
        return plane

    def __plane_from_point_and_line(self, point, line):
        child = ScenePlane.common_child(point, line)
        if child is not None:
            self._scene().select(child)
            return child
        plane = ScenePlane.by_point_and_line(point, line)
        self._push_object(plane, True)
        return plane

    def __plane_from_point_and_segment(self, point, segment):
        child = ScenePlane.common_child(point, segment)
        if child is not None:
            self._scene().select(child)
            return child
        plane = ScenePlane.by_point_and_segment(point, segment)
        self._push_object(plane, True)
        return plane

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
        for point in self.points:
            scene.remove_object(point)
        if self.plane is not None:
            scene.remove_object(self.plane)
        if self.line is not None:
            scene.remove_object(self.line)
        if self.segment is not None:
            scene.remove_object(self.segment)
        super(PlaneBuilder, self).cancel()


class EdgeBuilder(BaseBuilder):
    def __init__(self, scene: Scene):
        super(EdgeBuilder, self).__init__(scene)
        self.p1 = None
        self.__shift_used = False

    def on_mouse_pressed(self, event: QMouseEvent):
        if event.button() != Qt.LeftButton:
            return False

        shift = bool(event.modifiers() & Qt.ShiftModifier)
        if not shift and (self.__shift_used or self._ready):
            self.p1 = None
            self.__shift_used = False

        if self._ready and not shift \
                or not self._ready and not self.__shift_used:
            self._deselect_all_once()
        self._reset_ready()
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
            point = ScenePoint.by_pos(place)
            self._push_object(point, True)

        if self.p1:
            self.__edge_from_points(self.p1, point)
            if shift:
                self.__shift_used = True
                self._has_any_progress = False
            self._set_ready()
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
        if not self._ready and self._has_any_progress:
            scene.remove_object(self.p1)
        super(EdgeBuilder, self).cancel()


class DivisionBuilder(BaseBuilder):
    def __init__(self, scene):
        super(DivisionBuilder, self).__init__(scene)
        self.p = None
        self.__shift_used = False

    def on_mouse_pressed(self, event: QMouseEvent):
        if event.button() != Qt.LeftButton:
            return False

        shift = event.modifiers() & Qt.ShiftModifier
        if not shift and (self.__shift_used or self._ready):
            self.p = None
            self.__shift_used = False

        if self._ready and not shift \
                or not self._ready and not self.__shift_used:
            self._deselect_all_once()
        self._has_any_progress = True

        camera = self._scene().camera
        pos = extract_pos(event)

        mask = SELECT_POINT if self.p is None else SELECT_EDGE
        snap = self._try_snap_to(pos, mask=mask)

        if not snap:
            return False

        if not self.p:
            self.p = snap
            self._scene().select(self.p)
            return True

        edge = snap
        edge_parents = list(edge.parents)
        if self.p in edge_parents:
            return False

        had_face = SceneFace.common_child(self.p, edge)

        points = []
        for parent in edge.parents:
            if isinstance(parent, ScenePoint):
                points.append(parent)
        if len(points) != 2:
            print("Should not have happened")
            return False

        div_point_raw = edge.get_closest_point(camera, pos)
        if div_point_raw is None:
            return False
        div_point = ScenePoint.by_pos(div_point_raw)

        scene = self._scene()
        scene.remove_object(edge)

        edge1 = SceneEdge.by_two_points(points[0], div_point)
        edge2 = SceneEdge.by_two_points(points[1], div_point)
        connecting_edge = SceneEdge.by_two_points(self.p, div_point)

        self._push_object(div_point, True)
        self._push_object(edge1)
        self._push_object(edge2)
        self._push_object(connecting_edge, True)

        if had_face:
            face1 = SceneFace.by_three_points(points[0], div_point, self.p)
            face2 = SceneFace.by_three_points(points[1], div_point, self.p)
            face1.add_parents(edge1, connecting_edge,
                              SceneEdge.common_child(self.p, points[0]))
            face2.add_parents(edge2, connecting_edge,
                              SceneEdge.common_child(self.p, points[1]))
            self._push_object(face1)
            self._push_object(face2)

        self._set_ready()

        return True

    def cancel(self):
        self.p = None
        super(DivisionBuilder, self).cancel()


class FaceBuilder(BaseBuilder):
    def __init__(self, scene: Scene):
        super(FaceBuilder, self).__init__(scene)
        self.p1 = None
        self.p2 = None
        self.edge = None
        self.__shift_used = False

    def on_mouse_pressed(self, event: QMouseEvent):
        if event.button() != Qt.LeftButton:
            return False

        shift = event.modifiers() & Qt.ShiftModifier
        if not shift and (self.__shift_used or self._ready):
            self.p1 = None
            self.p2 = None
            self.edge = None
            self.__shift_used = False

        if self._ready and not shift \
                or not self._ready and not self.__shift_used:
            self._deselect_all_once()
        self._reset_ready()
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
            point = ScenePoint.by_pos(place)
            self._push_object(point, True)

        if self.p2 and self.edge is not None:
            edge2 = self.__edge_from_points(self.p2, point)
            edge3 = self.__edge_from_points(point, self.p1)
            face = self.__face_from_points(self.p1, self.p2, point)
            face.add_parents(self.edge, edge2, edge3)

            if shift:
                self.__shift_used = True
                self._has_any_progress = False
            self._set_ready()
            self.edge = edge3
            self.p2 = point
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
        if not self._ready and self._has_any_progress:
            if self.p1 is not None:
                scene.remove_object(self.p1)
            if self.p2 is not None:
                scene.remove_object(self.p2)
            if self.edge is not None:
                scene.remove_object(self.edge)
        return super(FaceBuilder, self).cancel()


class RectBuilder(BaseBuilder):
    def __init__(self, scene: Scene):
        super(RectBuilder, self).__init__(scene)
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
            point = ScenePoint.by_pos(place)
            self._push_object(point, True)

        if self.p1:
            self.__create_cube(point)
            self._set_ready()
            self.p1 = None
        else:
            self.p1 = point

        return True

    def __create_cube(self, p2):
        pos1 = self.p1.transform.translation
        pos2 = p2.transform.translation
        dx = glm.vec3(pos2.x - pos1.x, 0, 0)
        dy = glm.vec3(0, pos2.y - pos1.y, 0)
        dz = glm.vec3(0, 0, pos2.z - pos1.z)

        """
        Определяет расположение точки относительно смотрящего
         
        f - far  | n - near
        b - bot  | t - top
        l - left | r - right
        
        pos1 = fbl
        pos2 = ntr
        """

        fbl = pos1

        fbr = fbl + dx
        ftl = fbl + dy
        ftr = fbr + dy
        nbl = fbl + dz
        ntl = nbl + dy
        nbr = nbl + dx

        positions = [fbr, ftl, ftr, nbl, ntl, nbr]
        points = [self.p1] + [ScenePoint.by_pos(pos) for pos in positions] + [
            p2]
        for i in range(1, len(points) - 1):
            self._push_object(points[i], True)

        def make_face(first_index, second_index, third_index):
            first_point = points[first_index]
            second_point = points[second_index]
            third_point = points[third_index]
            face = self.__face_from_points(first_point, second_point,
                                           third_point)
            first_edge = self.__edge_from_points(first_point, second_point)
            second_edge = self.__edge_from_points(second_point, third_point)
            third_edge = self.__edge_from_points(third_point, first_point)
            face.add_parents(first_edge, second_edge, third_edge)

        make_face(1, 2, 3)
        make_face(0, 1, 2)
        make_face(0, 4, 5)
        make_face(0, 5, 2)
        make_face(0, 4, 1)
        make_face(2, 3, 7)
        make_face(2, 5, 7)
        make_face(4, 7, 5)
        make_face(4, 6, 7)
        make_face(1, 4, 6)
        make_face(1, 3, 6)
        make_face(3, 7, 6)

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
        return super(RectBuilder, self).cancel()
