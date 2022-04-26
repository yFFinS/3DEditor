from weakref import ref

from render_geometry import *
from scene_object_widget import SceneObjectWidget


class BaseBuilder:
    base_click_depth = 10

    def __init__(self, scene, scene_explorer):
        self.scene = ref(scene)
        self.scene_explorer = ref(scene_explorer)

    def push_object(self, obj):
        self.scene().add_object(obj)
        widget = SceneObjectWidget(obj)
        self.scene_explorer().add_scene_object_widget(widget)

    def on_click(self, pos):
        raise NotImplementedError

    def try_snap_to(self, x, y, mask):
        return self.scene().try_select_object(x, y, mask)


class PointBuilder(BaseBuilder):
    def on_click(self, pos):
        camera = self.scene().camera
        ray = camera.screen_to_world(pos)
        place = camera.translation + BaseBuilder.base_click_depth * ray

        point = ScenePoint(Point(place.x, place.y, place.z))
        self.push_object(point)
        self.scene_explorer().select_scene_object(point, True)
        return True


class LineBuilder(BaseBuilder):
    def __init__(self, scene, scene_explorer):
        super(LineBuilder, self).__init__(scene, scene_explorer)
        self.p1 = None

    def on_click(self, pos):
        camera = self.scene().camera
        snap = self.try_snap_to(pos.x, pos.y, SELECT_POINT)
        if snap:
            if snap == self.p1:
                return False
            point = snap
        else:
            ray = camera.screen_to_world(pos)
            place = camera.translation + BaseBuilder.base_click_depth * ray
            point = ScenePoint(Point(place.x, place.y, place.z))
            self.push_object(point)

        if self.p1:
            line = SceneLine(LineBy2Points(self.p1.point, point.point))
            self.push_object(line)
            self.scene_explorer().select_scene_object(line, True)
            return True
        else:
            self.scene_explorer().select_scene_object(point, True)
            self.p1 = point
            return False


class PlaneBuilder(BaseBuilder):
    def __init__(self, scene, scene_explorer):
        super(PlaneBuilder, self).__init__(scene, scene_explorer)
        self.p1 = None
        self.p2 = None

    def on_click(self, pos):
        camera = self.scene().camera
        snap = self.try_snap_to(pos.x, pos.y, SELECT_POINT)
        if snap:
            if snap == self.p1 or snap == self.p2:
                return False
            point = snap
        else:
            ray = camera.screen_to_world(pos)
            place = camera.translation + BaseBuilder.base_click_depth * ray
            point = ScenePoint(Point(place.x, place.y, place.z))
            self.push_object(point)
        if self.p2:
            plane = ScenePlane(PlaneBy3Points(self.p1.point, self.p2.point, point.point))
            self.push_object(plane)
            self.scene_explorer().select_scene_object(plane, True)
            return True
        elif self.p1:
            self.scene_explorer().select_scene_object(point, False)
            self.p2 = point
            return False
        else:
            self.scene_explorer().select_scene_object(point, True)
            self.p1 = point
            return False
