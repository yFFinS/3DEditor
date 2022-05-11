from typing import Iterable

import glm
import numpy as np
from numpy.typing import NDArray

from render.mesh import Mesh


class VirtualMesh:
    def __init__(self, shared_mesh: 'SharedMesh', offset: int, vertex_count: int, index_count: int):
        self.__shared_mesh = shared_mesh
        self.__vertex_count = vertex_count
        self.__index_count = index_count
        self.__offset = offset

    def set_positions(self, positions: NDArray[glm.vec3]):
        if len(positions) > self.__vertex_count:
            print("Выход за границы выделенного массива")
        self.__shared_mesh.set_positions_offset(positions, self.__offset)

    def set_colors(self, colors: NDArray[glm.vec4]):
        if len(colors) > self.__vertex_count:
            print("Выход за границы выделенного массива")
        self.__shared_mesh.set_colors_offset(colors, self.__offset)

    def set_indices(self, indices: NDArray[np.uint32]):
        if len(indices) > self.__index_count:
            print("Выход за границы выделенного массива")
        self.__shared_mesh.set_indices_offset(indices, self.__offset)


class SharedMesh(Mesh):
    def __init__(self, max_vertices):
        super(Mesh, self).__init__()
        self.__max_vertices = max_vertices

    def append_positions(self, positions: Iterable[glm.vec3]):
        self.__positions.extend(positions)

    def set_positions_offset(self, positions: NDArray[glm.vec3], offset: int):
        self.__

    def set_colors_offset(self, colors: NDArray[glm.vec4], offset: int):
        if len(colors) > self.__vertex_count:
            print("Выход за границы выделенного массива")
        self.__shared_mesh.set_colors()
        self.__vbo_colors.set_data(glm.sizeof(glm.vec4) * len(colors), colors)
        self.__colors = colors.copy()

    def set_indices_offset(self, indices: NDArray[np.uint32], offset: int):
        if len(indices) > self.__index_count:
            print("Выход за границы выделенного массива")
        self.__ibo.set_indices(indices)
        self.__indices = indices.copy()