from typing import Iterable

import glm
from OpenGL import GL
from numpy.typing import NDArray

from render.mesh import Mesh


class VirtualMesh:
    def __init__(self, shared_mesh: 'SharedMesh', vertex_offset: int,
                 vertex_count: int):
        self.__shared_mesh = shared_mesh
        self.__vertex_count = vertex_count
        self.__vertex_offset = vertex_offset

    def get_mesh(self):
        return self.__shared_mesh

    def set_positions(self, positions: NDArray[glm.vec3]):
        if len(positions) > self.__vertex_count:
            print("Выход за границы выделенного массива")
        self.__shared_mesh.set_positions_offset(positions, self.__vertex_offset)

    def set_colors(self, colors: NDArray[glm.vec4]):
        if len(colors) > self.__vertex_count:
            print("Выход за границы выделенного массива")
        self.__shared_mesh.set_colors_offset(colors, self.__vertex_offset)


class SharedMesh(Mesh):
    def __init__(self, max_vertices: int, render_mode: GL.GL_CONSTANT):
        super(SharedMesh, self).__init__()

        self.max_vertices = max_vertices
        self.used_vertices = 0
        self.render_mode = render_mode
        self._vbo_positions.reserve_size(max_vertices, glm.vec3)
        self._vbo_colors.reserve_size(max_vertices, glm.vec4)

    def set_positions_offset(self, positions: NDArray[glm.vec3], offset: int):
        self._vbo_positions.set_data_offset(
            glm.sizeof(glm.vec3) * len(positions),
            glm.sizeof(glm.vec3) * offset, positions)

    def set_colors_offset(self, colors: NDArray[glm.vec4], offset: int):
        self._vbo_colors.set_data_offset(glm.sizeof(glm.vec4) * len(colors),
                                         glm.sizeof(glm.vec4) * offset, colors)

    __meshes = []
    __base_vertex_count = 2 ** 14

    @staticmethod
    def request_mesh(vertices: int,
                     render_mode: GL.GL_CONSTANT) -> 'VirtualMesh':
        meshes = SharedMesh.__meshes
        for mesh in meshes:
            if (mesh.render_mode == render_mode and
                    mesh.used_vertices + vertices <= mesh.max_vertices):
                vmesh = VirtualMesh(mesh, mesh.used_vertices, vertices)
                mesh.used_vertices += vertices
                return vmesh
        smesh = SharedMesh(SharedMesh.__base_vertex_count, render_mode)
        smesh.used_vertices = vertices
        meshes.append(smesh)
        return VirtualMesh(smesh, 0, vertices)

    @staticmethod
    def get_all_meshes() -> Iterable['SharedMesh']:
        yield from SharedMesh.__meshes

    def get_vertex_count(self) -> int:
        return self.used_vertices
