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

        self.__points = {}
        self.__edges = {}
        self.__faces = {}
        self.__other = set()
        self.__planes = set()
        self.__lines = set()

        self.on_objects_added = Event()
        self.on_objects_removed = Event()
        self.on_objects_selected = Event()
        self.on_objects_deselected = Event()

    @staticmethod
    def __add_or_create(dest, obj):
        key = obj.mesh.get_mesh()
        if key not in dest:
            dest[key] = {obj}
        else:
            dest[key].add(obj)

    @staticmethod
    def __remove(src, obj):
        key = obj.mesh.get_mesh()
        src[key].remove(obj)
        if len(src[key]) == 0:
            src.pop(key)

    @profile
    def __store_object(self, scene_object):
        if isinstance(scene_object, ScenePoint):
            self.__add_or_create(self.__points, scene_object)
        elif isinstance(scene_object, SceneEdge):
            self.__add_or_create(self.__edges, scene_object)
        elif isinstance(scene_object, SceneFace):
            self.__add_or_create(self.__faces, scene_object)
        elif isinstance(scene_object, SceneLine):
            self.__lines.add(scene_object)
        elif isinstance(scene_object, ScenePlane):
            self.__planes.add(scene_object)
        else:
            self.__other.add(scene_object)

    @profile
    def __remove_from_storage(self, scene_object):
        if isinstance(scene_object, ScenePoint):
            self.__remove(self.__points, scene_object)
        elif isinstance(scene_object, SceneEdge):
            self.__remove(self.__edges, scene_object)
        elif isinstance(scene_object, SceneFace):
            self.__remove(self.__faces, scene_object)
        elif isinstance(scene_object, SceneLine):
            self.__lines.remove(scene_object)
        elif isinstance(scene_object, ScenePlane):
            self.__planes.remove(scene_object)
        else:
            self.__other.remove(scene_object)

    @profile
    def add_object(self, scene_object: RawSceneObject):
        self.__objects[scene_object.id] = scene_object
        self.__store_object(scene_object)
        if isinstance(scene_object, SceneObject):
            self.on_objects_added.invoke([scene_object])

    @profile
    def remove_object(self, scene_object: RawSceneObject):
        removed = self.__remove_object_silent(scene_object)
        self.on_objects_removed.invoke(removed)

    @profile
    def __remove_object_silent(self, scene_object: RawSceneObject) \
            -> list[RawSceneObject]:
        if scene_object.id not in self.__objects:
            return []

        self.__objects.pop(scene_object.id)
        self.__remove_from_storage(scene_object)
        if not isinstance(scene_object, SceneObject):
            return []
        removed = [scene_object]

        scene_object.on_delete()

        for child in scene_object.children:
            removed.extend(self.__remove_object_silent(child))
        return removed

    @profile
    def add_objects(self, scene_objects: Iterable[RawSceneObject]):
        invoke_list = []
        for obj in scene_objects:
            self.__objects[obj.id] = obj
            self.__store_object(obj)
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

    @profile
    def render_shared(self):
        for obj in self.__other:
            self.__render_single(obj)

        GL.glLineWidth(1.4)
        GL.glPointSize(6)

        for plane in self.__planes:
            self.__render_single(plane)

        def get_first_values(src):
            for v in src.values():
                yield next(iter(v))

        for face in get_first_values(self.__faces):
            self.__render_single_shared(face)

        GL.glPushAttrib(GL.GL_ENABLE_BIT)

        GL.glDisable(GL.GL_DEPTH_TEST)
        GL.glEnable(GL.GL_LINE_STIPPLE)

        for obj in self.__other:
            self.__render_single(obj)

        GL.glLineWidth(1.4)
        GL.glPointSize(6)

        for line in self.__lines:
            self.__render_single(line)

        for edge in get_first_values(self.__edges):
            self.__render_single_shared(edge)

        GL.glPopAttrib()

        GL.glDepthMask(GL.GL_FALSE)
        for line in self.__lines:
            self.__render_single(line)

        for edge in get_first_values(self.__edges):
            self.__render_single_shared(edge)

        GL.glDepthMask(GL.GL_TRUE)

        GL.glDisable(GL.GL_DEPTH_TEST)

        for point in get_first_values(self.__points):
            self.__render_single_shared(point)

        GL.glEnable(GL.GL_DEPTH_TEST)

    @profile
    def __render_single_shared(self, scene_object):
        mesh = scene_object.mesh.get_mesh()
        shader = scene_object.shader_program

        shader.use()
        shader.set_mat4("Batch.Mat_PV", self.camera.proj_view_matrix)

        mesh.bind_vba()
        GL.glDrawArrays(scene_object.render_mode, 0, mesh.get_vertex_count())
        mesh.unbind_vba()

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
                print(f"Weight must be between 0 and 1. Was {weight} at {obj}.")
                continue
            if weight > select_w:
                select_w = weight
                to_select = obj
        return to_select
