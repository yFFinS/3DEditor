from PyQt5.QtGui import QMouseEvent
from scene.scene import *


class GLSceneInterface:
    on_scene_changed: Event

    def create_division(self):
        raise NotImplementedError

    def move(self, move: glm.vec3):
        pass

    def get_scene(self) -> Scene:
        raise NotImplementedError

    def redraw(self):
        raise NotImplementedError

    def unload(self):
        raise NotImplementedError

    def no_action(self):
        raise NotImplementedError

    def move_object(self):
        raise NotImplementedError

    def create_point(self):
        raise NotImplementedError

    def create_line(self):
        raise NotImplementedError

    def create_plane(self):
        raise NotImplementedError

    def create_edge(self):
        raise NotImplementedError

    def create_face(self):
        raise NotImplementedError

    def create_rect(self):
        raise NotImplementedError

    def try_select_scene_object(self, event: QMouseEvent) -> bool:
        raise NotImplementedError
