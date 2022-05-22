import uuid
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

    def clear(self):
        self.__shared_mesh.clear_offset(self.__vertex_count,
                                        self.__vertex_offset)


class SharedMesh(Mesh):
    BATCH_SIZE = 2 ** 16

    def __init__(self, max_vertices: int, render_mode: GL.GL_CONSTANT):
        super(SharedMesh, self).__init__()

        self.__id = uuid.uuid4()

        self.max_vertices = max_vertices
        self.used_vertices = 0
        self.render_mode = render_mode
        self._vbo_positions.reserve_size(max_vertices, glm.vec3)
        self._vbo_colors.reserve_size(max_vertices, glm.vec4)

    def clear_offset(self, vertices: int, offset: int):
        self._vbo_positions.clear_offset(glm.sizeof(glm.vec3) * vertices,
                                         glm.sizeof(glm.vec3) * offset)
        self._vbo_colors.clear_offset(glm.sizeof(glm.vec4) * vertices,
                                      glm.sizeof(glm.vec4) * offset)

    def set_positions_offset(self, positions: NDArray[glm.vec3], offset: int):
        self._vbo_positions.set_data_offset(
            glm.sizeof(glm.vec3) * len(positions),
            glm.sizeof(glm.vec3) * offset, positions)

    def set_colors_offset(self, colors: NDArray[glm.vec4], offset: int):
        self._vbo_colors.set_data_offset(glm.sizeof(glm.vec4) * len(colors),
                                         glm.sizeof(glm.vec4) * offset, colors)

    __meshes = []
    __available = []

    @staticmethod
    def request_mesh(vertices: int,
                     render_mode: GL.GL_CONSTANT) -> 'VirtualMesh':
        meshes = SharedMesh.__available
        meshes_with_matching_render_mode = [mesh for mesh in meshes if
                                            mesh.render_mode == render_mode]
        for mesh in meshes_with_matching_render_mode:
            if mesh.used_vertices + vertices <= mesh.max_vertices:
                vmesh = VirtualMesh(mesh, mesh.used_vertices, vertices)
                mesh.used_vertices += vertices
                return vmesh
            else:
                meshes.remove(mesh)

        smesh = SharedMesh(SharedMesh.BATCH_SIZE, render_mode)
        smesh.used_vertices = vertices
        meshes.append(smesh)
        SharedMesh.__meshes.append(smesh)

        return VirtualMesh(smesh, 0, vertices)

    @staticmethod
    def clear_meshes():
        for mesh in SharedMesh.get_all_meshes():
            mesh.dispose()
        SharedMesh.__meshes.clear()
        SharedMesh.__available.clear()

    @staticmethod
    def get_all_meshes() -> Iterable['SharedMesh']:
        yield from SharedMesh.__meshes

    def get_vertex_count(self) -> int:
        return self.used_vertices

    def __hash__(self):
        return hash(self.__id)