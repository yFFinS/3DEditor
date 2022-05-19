import itertools

import glm
import numpy as np

from typing import Iterable, Optional, Union

from OpenGL import GL

from profiling.profiler import profile
from core.event import Event
from render.shared_vbo import SharedMesh
from .camera import Camera
from .render_geometry import ScenePlane, ScenePoint, SceneEdge, SceneFace, \
    SceneLine
from .scene_object import SceneObject, RawSceneObject


class Scene:
    def __init__(self):
        self.__objects = {}
        self.camera: Optional[Camera] = None

        self.on_objects_added = Event()
        self.on_objects_removed = Event()
        self.on_objects_selected = Event()
        self.on_objects_deselected = Event()

    @profile
    def add_object(self, scene_object: RawSceneObject):
        self.__objects[scene_object.id] = scene_object
        if isinstance(scene_object, SceneObject):
            self.on_objects_added.invoke([scene_object])

    @profile
    def remove_object(self, scene_object: RawSceneObject):
        removed = self.__remove_object_silent(scene_object)
        self.on_objects_removed.invoke(removed)

    @profile
    def __remove_object_silent(self, scene_object: RawSceneObject) -> list[
        RawSceneObject]:
        if scene_object.id not in self.__objects:
            return []
        self.__objects.pop(scene_object.id)
        if not isinstance(scene_object, SceneObject):
            return []
        removed = [scene_object]
        if scene_object.selected:
            self.deselect(scene_object)
        for child in scene_object.children:
            removed.extend(self.__remove_object_silent(child))
        return removed

    @profile
    def add_objects(self, scene_objects: Iterable[RawSceneObject]):
        invoke_list = []
        for obj in scene_objects:
            self.__objects[obj.id] = obj
            if isinstance(obj, SceneObject):
                invoke_list.append(obj)
        self.on_objects_added.invoke(invoke_list)

    @profile
    def remove_objects(self, scene_objects: Iterable[RawSceneObject]):
        removed = []
        for obj in scene_objects:
            removed.extend(self.__remove_object_silent(obj))
        self.on_objects_removed.invoke(removed)

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

    @profile
    def render(self):
        if not self.camera:
            return

        layers, transparent = self.__group_by_render_layer(self.all_objects)

        for layer in layers:
            others, points, lines, triangles \
                = self.__group_objects_by_render_params(layer)

            for other in others:
                self.__render_single(other)

            if triangles:
                for triangle in triangles:
                    self.__render_single(triangle)

            GL.glDepthMask(GL.GL_FALSE)
            if lines:
                GL.glLineWidth(1.4)
                for line in lines:
                    self.__render_single(line)

            if points:
                GL.glPointSize(6)
                for point in points:
                    self.__render_single(point)
            GL.glDepthMask(GL.GL_TRUE)

        for tr in transparent:
            self.__render_single(tr)

    @staticmethod
    def __group_by_object_type(scene_objects):
        other, instanced, lines, planes = [], [], [], []
        for obj in scene_objects:
            if isinstance(obj, (ScenePoint, SceneEdge, SceneFace)):
                instanced.append(obj)
            elif isinstance(obj, SceneLine):
                lines.append(obj)
            elif isinstance(obj, ScenePlane):
                planes.append(obj)
            else:
                other.append(obj)
        return other, instanced, lines, planes

    def render_shared(self):
        objects = self.all_objects
        other, instanced, lines, planes = self.__group_by_object_type(objects)

        for obj in other:
            self.__render_single(obj)

        GL.glLineWidth(1.4)
        GL.glPointSize(6)

        for plane in planes:
            self.__render_single(plane)

        points, edges, faces = [self.__group_by_mesh(temp) for temp in
                                self.__group_by_render_mode(instanced)]

        for face in faces.values():
            self.__render_single_shared(face[0])

        GL.glDepthMask(GL.GL_FALSE)
        for line in lines:
            self.__render_single(line)

        for edge in edges.values():
            self.__render_single_shared(edge[0])

        for point in points.values():
            self.__render_single_shared(point[0])
        GL.glDepthMask(GL.GL_TRUE)

    def __render_single_shared(self, scene_object):
        mesh = scene_object.mesh.get_mesh()
        shader = scene_object.shader_program

        shader.use()
        shader.set_mat4("Batch.Mat_PV", self.camera.proj_view_matrix)

        mesh.bind_vba()
        GL.glDrawArrays(scene_object.render_mode, 0, mesh.get_vertex_count())
        mesh.unbind_vba()

    @staticmethod
    def __group_by_render_mode(scene_objects):
        points, lines, triangles = [], [], []
        for scene_object in scene_objects:
            if scene_object.render_mode == GL.GL_POINTS:
                points.append(scene_object)
            elif scene_object.render_mode == GL.GL_LINES:
                lines.append(scene_object)
            else:
                triangles.append(scene_object)
        return points, lines, triangles

    @staticmethod
    def __group_by_mesh(scene_objects):
        result = {}
        for scene_object in scene_objects:
            mesh = scene_object.mesh.get_mesh()
            if mesh not in result:
                result[mesh] = []
            result[mesh].append(scene_object)
        return result

    @staticmethod
    @profile
    def __group_by_render_layer(objects):
        groups = {}
        transparent = []
        for obj in objects:
            if isinstance(obj, ScenePlane):
                transparent.append(obj)
                continue
            layer = obj.render_layer
            if layer not in groups:
                groups[layer] = [obj]
            else:
                groups[layer].append(obj)

        result = [groups[key] for key in sorted(groups)]
        return result, transparent

    @staticmethod
    @profile
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

    def __render_instanced(self, scene_objects: list[RawSceneObject]):
        raise NotImplemented
        # for obj in scene_objects:
        #     obj.prepare_render(self.camera)
        #
        # mvps = [obj.get_render_mat(self.camera) for obj in scene_objects]
        #
        # # Предполагается, что у всех объектов один шейдер
        # shader = scene_objects[0].shader_program
        # shader.use()
        # shader.set_mat4("Instance.MVP", mvp)
        #
        # selected_value = 1 if isinstance(scene_object, SceneObject) and scene_object.selected else -1
        # scene_object.shader_program.set_float("Instance.Selected",
        #                                       selected_value)
        #
        # scene_object.mesh.bind_vba()
        # indices = scene_object.mesh.get_index_count()
        # if indices != 0:
        #     GL.glDrawElements(scene_object.render_mode,
        #                       indices, GL.GL_UNSIGNED_INT, None)
        # else:
        #     GL.glDrawArrays(scene_object.render_mode,
        #                     0, scene_object.mesh.get_vertex_count())
        # scene_object.mesh.unbind_vba()
        #
        # for obj in scene_objects:
        #     obj.render_completed(self.camera)

    @profile
    def __render_single(self, scene_object: RawSceneObject):
        scene_object.prepare_render(self.camera)

        mvp = scene_object.get_render_mat(self.camera)

        scene_object.shader_program.use()
        scene_object.shader_program.set_mat4("Instance.MVP", mvp)

        selected_value = 1 if isinstance(scene_object,
                                         SceneObject) and scene_object.selected else -1
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

    @profile
    def select(self, scene_objects: Union[SceneObject, list[SceneObject]]):
        if not scene_objects:
            return

        if not isinstance(scene_objects, list):
            scene_objects = [scene_objects]

        event_args = []
        for obj in filter(lambda o: not o.selected, scene_objects):
            obj.set_selected(True)
            obj.selected = True
            event_args.append(obj)

        if event_args:
            self.on_objects_selected.invoke(scene_objects)

    @profile
    def deselect_all(self):
        self.deselect([obj for obj in self.objects if obj.selected])

    @profile
    def deselect(self, scene_objects: Union[SceneObject, list[SceneObject]]):
        if not scene_objects:
            return

        if not isinstance(scene_objects, list):
            scene_objects = [scene_objects]

        event_args = []
        for obj in filter(lambda o: o.selected, scene_objects):
            obj.set_selected(False)
            obj.selected = False
            event_args.append(obj)

        if event_args:
            self.on_objects_deselected.invoke(scene_objects)

    @profile
    def find_selectable(self, screen_pos: glm.vec2, mask: int = 0xFFFFFFFF,
                        allow_selected: bool = False) -> \
            Optional[SceneObject]:
        to_select = None
        select_w = -1
        for obj in self.objects:
            if not allow_selected and obj.selected or (
                    mask & obj.selection_mask) == 0:
                continue
            weight = obj.get_selection_weight(self.camera, screen_pos)
            if np.isnan(weight):
                continue
            if weight < 0 or weight > 1:
                print(f"Вес должен быть от 0 до 1. Был {weight} у {obj}.")
                continue
            if weight > select_w:
                select_w = weight
                to_select = obj
        return to_select
