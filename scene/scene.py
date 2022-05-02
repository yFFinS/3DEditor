import glm
import numpy as np

from typing import Iterable, Optional, Union

from OpenGL import GL

from core.event import Event
from .camera import Camera
from .scene_object import SceneObject, RawSceneObject


class Scene:
    def __init__(self):
        self.__objects = {}
        self.camera: Optional[Camera] = None

        self.on_object_added = Event()
        self.on_object_removed = Event()
        self.on_objects_selected = Event()
        self.on_objects_deselected = Event()

    def add_object(self, scene_object: RawSceneObject):
        self.__objects[scene_object.id] = scene_object
        if isinstance(scene_object, SceneObject):
            self.on_object_added.invoke(scene_object)

    def remove_object(self, scene_object: RawSceneObject):
        if scene_object.id not in self.__objects:
            return
        self.__objects.pop(scene_object.id)
        if not isinstance(scene_object, SceneObject):
            return
        if scene_object.selected:
            self.deselect(scene_object)
        for child in scene_object.children:
            self.remove_object(child)
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

        layers = self.__group_by_render_layer(self.all_objects)
        for layer in layers:
            others, points, lines, triangles = self.__group_objects_by_render_params(layer)

            for other in others:
                self.__render_object(other)

            if triangles:
                for triangle in triangles:
                    self.__render_object(triangle)

            GL.glDepthMask(GL.GL_FALSE)
            if lines:
                GL.glLineWidth(1.4)
                for line in lines:
                    self.__render_object(line)

            if points:
                GL.glPointSize(6)
                for point in points:
                    self.__render_object(point)
            GL.glDepthMask(GL.GL_TRUE)

    @staticmethod
    def __group_by_render_layer(objects):
        groups = {}
        for obj in objects:
            layer = obj.render_layer
            if layer not in groups:
                groups[layer] = [obj]
            else:
                groups[layer].append(obj)
        for key in sorted(groups):
            yield groups[key]

    @staticmethod
    def __group_objects_by_render_params(objects):
        others, points, lines, triangles = [], [], [], []
        for obj in objects:
            if not isinstance(obj, SceneObject):
                others.append(obj)
                continue
            if obj.render_mode == GL.GL_TRIANGLES:
                triangles.append(obj)
            elif obj.render_mode == GL.GL_LINES:
                lines.append(obj)
            elif obj.render_mode == GL.GL_POINTS:
                points.append(obj)
            else:
                others.append(obj)
        return others, points, lines, triangles

    def __render_object(self, scene_object: RawSceneObject):
        scene_object.prepare_render(self.camera)

        mvp = scene_object.get_render_mat(self.camera)

        scene_object.shader_program.use()
        scene_object.shader_program.set_mat4("Instance.MVP", mvp)

        selected_value = 1 if isinstance(scene_object, SceneObject) and scene_object.selected else -1
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

        scene_object.render_completed(self.camera)

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

    def deselect_all(self):
        self.deselect([obj for obj in self.objects if obj.selected])

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

    def find_selectable(self, screen_pos: glm.vec2, mask: int = 0xFFFFFFFF, allow_selected: bool = False) -> \
            Optional[SceneObject]:
        to_select = None
        select_w = -1
        for obj in self.objects:
            if not allow_selected and obj.selected or (mask & obj.selection_mask) == 0:
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
