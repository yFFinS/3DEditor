import glm

from weakref import ref
from typing import Iterable, Optional, Union

import numpy as np

from core.event import Event
from .interfaces import SceneEventListener
from .scene_object import SceneObject


class Scene:
    def __init__(self):
        self.__objects = []
        self.camera = None

        self.on_object_added = Event()
        self.on_object_removed = Event()
        self.on_objects_selected = Event()
        self.on_objects_deselected = Event()

    def add_object(self, scene_object: SceneObject):
        self.__objects.append(scene_object)
        self.on_object_added.invoke(scene_object)

    def remove_object(self, scene_object: SceneObject):
        self.__objects.remove(scene_object)
        self.on_object_removed.invoke(scene_object)

    @property
    def objects(self) -> Iterable[SceneObject]:
        yield from self.__objects

    def load(self, filename: str):
        pass

    def render(self):
        if not self.camera:
            return

        objects = [(int(obj.selected), obj.render_layer, -i, obj) for i, obj in enumerate(self.objects)]
        for *_, obj in sorted(objects):
            obj.render(self.camera)

    def unload(self):
        self.__objects.clear()
        self.camera = None

    def select(self, scene_objects: Union[SceneObject, list[SceneObject]]):
        if isinstance(scene_objects, list):
            for obj in scene_objects:
                obj.selected = True
        else:
            scene_objects.selected = True
            scene_objects = [scene_objects]
        self.on_objects_selected.invoke(scene_objects)

    def deselect(self, scene_objects: Union[SceneObject, list[SceneObject]]):
        if isinstance(scene_objects, list):
            for obj in scene_objects:
                obj.selected = False
        else:
            scene_objects.selected = False
            scene_objects = [scene_objects]
        self.on_objects_deselected.invoke(scene_objects)

    def find_selectable(self, screen_pos: glm.vec2, mask: int = 0xFFFFFFFF) -> Optional[SceneObject]:
        to_select = None
        select_w = -1
        for obj in self.objects:
            if obj.selected or (mask & obj.selection_mask) == 0:
                continue
            adjusted_pos = glm.vec2(screen_pos.x, self.camera.height - screen_pos.y)
            weight = obj.get_selection_weight(self.camera, adjusted_pos)
            if np.isnan(weight):
                continue
            if weight < 0 or weight > 1:
                print(f"Вес должен быть от 0 до 1. Был {weight} у {obj}.")
                continue
            if weight > select_w:
                select_w = weight
                to_select = obj
        return to_select
