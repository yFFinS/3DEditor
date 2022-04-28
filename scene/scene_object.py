import abc
import uuid
from abc import ABC
from typing import Optional

import glm
import numpy as np
from OpenGL import GL

from core.Base_geometry_objects import BaseGeometryObject
from scene.camera import Camera
from render.mesh import Mesh
from scene.transform import Transform


class RawSceneObject(ABC):
    SHADER_PROGRAM = None

    def __init__(self, obj_id: uuid.UUID = None):
        self.__id = obj_id if obj_id is not None else uuid.uuid4()
        self.transform = Transform()

        self.mesh = Mesh()
        self.shader_program = SceneObject.SHADER_PROGRAM
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


class SceneObject(RawSceneObject):
    SHADER_PROGRAM = None

    def __init__(self, primitive: BaseGeometryObject):
        super(SceneObject, self).__init__(primitive.id)
        
        self.__primitive = primitive
        self.selected = False
        self.selection_mask = 0

    @property
    def primitive(self) -> BaseGeometryObject:
        return self.__primitive

    @property
    def name(self) -> str:
        return self.primitive.name

    @property
    def type(self) -> str:
        return self.primitive.type

    def set_position(self, pos: glm.vec3):
        self.transform.translation = pos

    def get_selection_weight(self, camera: Camera, click_pos: glm.vec2) -> float:
        """
            Возвращает значение от 0 до 1. Чем больше значение, тем больше приоритет выбора этого объекта.
            Возвращает NaN, если объект выбирать не нужно.
        """
        return np.nan
