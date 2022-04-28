import glm
import numpy as np

from typing import Iterable, Optional, Union

from OpenGL import GL

from core.event import Event
from .scene_object import SceneObject, RawSceneObject


class Scene:
    def __init__(self):
        self.__objects = {}
        self.camera = None

        self.on_object_added = Event()
        self.on_object_removed = Event()
        self.on_objects_selected = Event()
        self.on_objects_deselected = Event()

    def add_object(self, scene_object: RawSceneObject):
        self.__objects[scene_object.id] = scene_object
        if isinstance(scene_object, SceneObject):
            self.on_object_added.invoke(scene_object)

    def remove_object(self, scene_object: RawSceneObject):
        self.__objects.pop(scene_object.id)
        if isinstance(scene_object, SceneObject):
            self.on_object_removed.invoke(scene_object)

    @property
    def all_objects(self) -> Iterable[RawSceneObject]:
        yield from self.__objects.values()

    @property
    def objects(self) -> Iterable[SceneObject]:
        for obj in self.all_objects:
            if isinstance(obj, SceneObject):
                yield obj

    def load(self, filename: str):
        pass

    def render(self):
        if not self.camera:
            return

        objects = [(int(isinstance(obj, SceneObject) and obj.selected),
                    obj.render_layer, -i, obj) for i, obj in
                   enumerate(self.all_objects)]
        for *_, obj in objects:
            obj.prepare_render(self.camera)
        for *_, obj in sorted(objects):
            self.__render_object(obj)

    def __render_object(self, scene_object: RawSceneObject):
        mvp = scene_object.get_render_mat(self.camera)

        scene_object.shader_program.use()
        scene_object.shader_program.set_mat4("Instance.MVP", mvp)

        selected_value = 1 if isinstance(scene_object, SceneObject) \
                              and scene_object.selected else -1
        scene_object.shader_program.set_float("Instance.Selected",
                                              selected_value)

        scene_object.mesh.bind_vba()
        indices = scene_object.mesh.get_index_count()
        if indices != 0:
            GL.glDrawElements(scene_object.render_mode,
                              indices, GL.GL_UNSIGNED_INT, None)
        else:
            GL.glDrawArrays(scene_object.render_mode,
                            0, scene_object.mesh.get_vertex_count())
        scene_object.mesh.unbind_vba()

    def unload(self):
        self.__objects.clear()
        self.camera = None

    def select(self, scene_objects: Union[SceneObject, list[SceneObject]]):
        if not scene_objects:
            return

        if not isinstance(scene_objects, list):
            scene_objects = [scene_objects]

        event_args = []
        for obj in filter(lambda o: not o.selected, scene_objects):
            obj.selected = True
            event_args.append(obj)

        if event_args:
            self.on_objects_selected.invoke(scene_objects)

    def deselect(self, scene_objects: Union[SceneObject, list[SceneObject]]):
        if not scene_objects:
            return

        if not isinstance(scene_objects, list):
            scene_objects = [scene_objects]

        event_args = []
        for obj in filter(lambda o: o.selected, scene_objects):
            obj.selected = False
            event_args.append(obj)

        if event_args:
            self.on_objects_deselected.invoke(scene_objects)

    def find_selectable(self, screen_pos: glm.vec2, mask: int = 0xFFFFFFFF) -> \
            Optional[SceneObject]:
        to_select = None
        select_w = -1
        for obj in self.objects:
            if obj.selected or (mask & obj.selection_mask) == 0:
                continue
            adjusted_pos = glm.vec2(screen_pos.x,
                                    self.camera.height - screen_pos.y)
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
