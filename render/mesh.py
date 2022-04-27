from typing import Iterable

import glm
import numpy as np
import numpy.typing as npt
from OpenGL import GL as GL

from helpers import empty_uint32_array, empty_float32_array
from render.buffers import VertexBuffer, IndexBuffer
from render.vertex_array import VertexArray


class Mesh:
    def __init__(self):
        self.__vba = VertexArray()

        self.__vbo_positions = VertexBuffer()
        self.__vbo_colors = VertexBuffer()
        self.__ibo = IndexBuffer()

        self.__vba.bind_vertex_buffer(self.__vbo_positions, 0, 0, 3, GL.GL_FLOAT, 12)
        self.__vba.bind_vertex_buffer(self.__vbo_colors, 1, 1, 4, GL.GL_FLOAT, 16)
        self.__vba.bind_index_buffer(self.__ibo)

        self.__indices = empty_uint32_array()
        self.__positions = empty_float32_array()
        self.__colors = empty_float32_array()

    def set_positions(self, positions: npt.NDArray[glm.vec3]):
        self.__vbo_positions.set_data(glm.sizeof(glm.vec3) * len(positions), positions)
        self.__positions = positions.copy()

    def set_colors(self, colors: npt.NDArray[glm.vec4]):
        self.__vbo_colors.set_data(glm.sizeof(glm.vec4) * len(colors), colors)
        self.__colors = colors.copy()

    def set_indices(self, indices: npt.NDArray[np.uint32]):
        self.__ibo.set_indices(indices)
        self.__indices = indices.copy()

    def get_positions(self) -> Iterable[glm.vec3]:
        yield from self.__positions

    def get_colors(self) -> Iterable[glm.vec4]:
        yield from self.__colors

    def get_indices(self) -> Iterable[np.uint32]:
        yield from self.__indices

    def get_index_count(self) -> int:
        return len(self.__indices)

    def get_vertex_count(self) -> int:
        return len(self.__positions)

    def bind_vba(self):
        self.__vba.bind()

    def unbind_vba(self):
        self.__vba.unbind()
