from OpenGL import GL as GL

from helpers import as_uint32_array
from render.buffers import IndexBuffer, VertexBuffer
from render.unmanaged import UnmanagedResource


class VertexArray(UnmanagedResource):
    def __init__(self):
        super(VertexArray, self).__init__()
        self.__id = GL.glGenVertexArrays(1)
        self.bind()

    @property
    def id(self):
        return self.__id

    def dispose(self):
        GL.glDeleteVertexArrays(1, as_uint32_array(self.__id))
        self.__id = -1

    def bind(self):
        GL.glBindVertexArray(self.__id)

    @staticmethod
    def unbind():
        GL.glBindVertexArray(0)

    def bind_vertex_buffer(self, vbo: VertexBuffer, binding: int,
                           attribute: int, element_count: int, attr_type: GL.Constant, stride: int):
        GL.glEnableVertexArrayAttrib(self.__id, attribute)
        GL.glVertexArrayAttribFormat(self.__id, attribute, element_count, attr_type, False, 0)
        GL.glVertexArrayAttribBinding(self.__id, attribute, binding)
        GL.glVertexArrayVertexBuffer(self.__id, binding, vbo.id, 0, stride)

    def bind_index_buffer(self, ibo: IndexBuffer):
        GL.glVertexArrayElementBuffer(self.__id, ibo.id)
