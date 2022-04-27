from .scene_object import SceneObject
from typing import Iterable


class SceneInterface:
    def add_object(self, scene_object: SceneObject):
        raise NotImplementedError

    def remove_object(self, scene_object: SceneObject):
        raise NotImplementedError

    @property
    def objects(self) -> Iterable[SceneObject]:
        raise NotImplementedError


class SceneEventListener:
    def on_object_removed(self, scene_object: SceneObject):
        raise NotImplementedError

    def on_object_added(self, scene_object: SceneObject):
        raise NotImplementedError

    def on_objects_selected(self, scene_objects: list[SceneObject]):
        raise NotImplementedError

    def on_objects_deselected(self, scene_objects: list[SceneObject]):
        raise NotImplementedError
