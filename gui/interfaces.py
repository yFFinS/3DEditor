from PyQt5.QtGui import QMouseEvent

from scene import *
from geometry_builder import *


class UpdateReceiverInterface:
    def update(self):
        raise NotImplementedError


class SceneActionsInterface:
    def action_move(self):
        raise NotImplementedError

    def action_point(self):
        raise NotImplementedError

    def action_line(self):
        raise NotImplementedError

    def action_plane(self):
        raise NotImplementedError


class GlSceneInterface:
    def get_scene(self) -> Scene:
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

    def try_select_scene_object(self, event: QMouseEvent) -> bool:
        raise NotImplementedError


class SceneExplorerInterface:
    def add_scene_object(self, scene_object: SceneObject):
        raise NotImplementedError

    def clear_selection(self):
        raise NotImplementedError

    def select_scene_object(self, scene_object: SceneObject,
                            deselect_others: bool = False):
        raise NotImplementedError

    def deselect_scene_object(self, scene_object: SceneObject):
        raise NotImplementedError


class SceneObjectPropertiesInterface:
    def clear(self):
        raise NotImplementedError

    def set_scene_object(self, scene_object: SceneObject):
        raise NotImplementedError

    def update_properties(self):
        raise NotImplementedError


class SceneObjectListInterface:
    def delete_selected(self):
        raise NotImplementedError

    def deselect_all(self):
        raise NotImplementedError

    def add_scene_object(self, scene_object: SceneObject):
        raise NotImplementedError

    def select_scene_object(self, scene_object: SceneObject,
                            deselect_others: bool = False):
        raise NotImplementedError

