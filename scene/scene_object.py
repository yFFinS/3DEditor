import uuid
from typing import Iterable, Type, Optional, TypeVar, final
from weakref import ref
from abc import ABC

import glm
import numpy as np
from OpenGL import GL

from core.Base_geometry_objects import BaseGeometryObject
from core.event import Event
from scene.camera import Camera
from scene.transform import Transform


class RawSceneObject(ABC):
    SHADER_PROGRAM = None

    def __init__(self, obj_id: uuid.UUID = None):
        self.__id = obj_id if obj_id is not None else uuid.uuid4()
        self.transform: Transform = Transform()

        self.mesh = None
        self.shader_program = self.SHADER_PROGRAM
        self.render_mode = GL.GL_TRIANGLES
        self.render_layer = 0

    @property
    def id(self) -> uuid.UUID:
        return self.__id

    def __hash__(self):
        return self.id.__hash__()

    def get_render_mat(self, camera: Camera) -> glm.mat4:
        return camera.get_mvp(self.transform.model_matrix)

    def prepare_render(self, camera: Camera):
        pass

    def render_completed(self, camera: Camera):
        pass


class SceneObject(RawSceneObject):
    SHADER_PROGRAM = None

    def __init__(self, primitive: BaseGeometryObject, *parents: 'SceneObject'):
        super(SceneObject, self).__init__(primitive.id)

        self.__primitive = primitive
        self.selected = False
        self.selection_mask = 0
        self.on_updated = Event()

        self.__parents = {}
        self.__children = {}
        self.add_parents(*parents)
        for parent in parents:
            parent.add_children(self)

    def post_update(self):
        self.on_updated.invoke(self)

    _T = TypeVar("_T")

    @classmethod
    def common_child(cls: Type[_T], *objects: 'SceneObject') -> Optional[_T]:
        children_sets = [
            set(child_id for child_id, child in obj.__children.items()
                if isinstance(child, cls)) for obj in objects]
        intersection = set.intersection(*children_sets)
        return objects[0].__children[
            next(iter(intersection))] if intersection else None

    @property
    def parents(self) -> Iterable['SceneObject']:
        for parent in self.__parents.values():
            yield parent()

    @property
    def children(self) -> Iterable['SceneObject']:
        yield from self.__children.values()

    def add_parents(self, *parents: 'SceneObject'):
        for parent in parents:
            if parent.id not in self.__parents:
                self.__parents[parent.id] = ref(parent)
                parent.add_children(self)

    def remove_parents(self, *parents: 'SceneObject'):
        for parent in parents:
            if parent.id in self.__parents:
                self.__parents.pop(parent.id)
                parent.remove_children(self)

    def add_children(self, *children: 'SceneObject'):
        for child in children:
            if child.id not in self.__children:
                self.__children[child.id] = child
                child.add_parents(self)

    def remove_children(self, *children: 'SceneObject'):
        for child in children:
            if child.id in self.__children:
                self.__children.pop(child.id)
                child.remove_parents(self)

    @property
    def primitive(self) -> BaseGeometryObject:
        return self.__primitive

    @property
    def name(self) -> str:
        return self.primitive.name

    @property
    def type(self) -> str:
        return self.primitive.type

    @final
    def update_position(self, pos: glm.vec3):
        self.update_hierarchy_position(pos, set())

    def update_hierarchy_position(self, pos: glm.vec3,
                                  ignored: set['SceneObject']):
        self.transform.translation = pos

    def on_parent_position_updated(self, parent: 'SceneObject'):
        pass

    def set_selected(self, value: bool):
        pass

    def get_selection_weight(self, camera: Camera,
                             click_pos: glm.vec2) -> float:
        """
            Возвращает значение от 0 до 1. Чем больше значение, тем больше
             приоритет выбора этого объекта.
            Возвращает NaN, если объект выбирать не нужно.
        """
        return np.nan
