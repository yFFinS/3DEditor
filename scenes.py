from buffers import *
from helpers import empty_float32_array, empty_uint32_array


class RenderableObject:
    def __init__(self):
        self.__vba = VertexArray()

        self.__vbo = VertexBuffer()
        self.__ibo = IndexBuffer()

        self.__vba.bind_vertex_buffer(self.__vbo, 0, 0, 3, GL.GL_FLOAT, 12)
        self.__vba.bind_index_buffer(self.__ibo)

        self.__shader_program = None

        self.__indices = empty_uint32_array()
        self.__positions = empty_float32_array()

    def set_shader_program(self, shader):
        self.__shader_program = shader

    def set_positions(self, positions):
        self.__vbo.set_data(positions)
        self.__positions = positions.copy()

    def set_indices(self, indices):
        self.__ibo.set_indices(indices)
        self.__indices = indices.copy()

    def get_positions(self):
        return self.__positions.copy()

    def get_indices(self):
        return self.__indices.copy()

    def render(self):
        self.__shader_program.use()
        self.__vba.bind()
        GL.glDrawElements(GL.GL_TRIANGLES, len(self.__indices), GL.GL_UNSIGNED_INT, None)
        self.__vba.unbind()


class Scene:
    def __init__(self):
        self.__objects: list[RenderableObject] = []

    def create_object(self) -> RenderableObject:
        obj = RenderableObject()
        self.__objects.append(obj)
        return obj

    def render(self):
        for obj in self.__objects:
            obj.render()

    def unload(self):
        self.__objects.clear()
