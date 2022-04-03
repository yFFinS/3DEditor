import OpenGL.GL as GL

from common import UnmanagedResource
from helpers import as_uint32_array


class Buffer(UnmanagedResource):
    def __init__(self, target):
        super(Buffer, self).__init__()
        self.__id = GL.glGenBuffers(1)
        self.__target = target
        self.bind()

    @property
    def id(self):
        return self.__id

    def bind(self):
        GL.glBindBuffer(self.__target, self.__id)

    def unbind(self):
        GL.glBindBuffer(self.__target, 0)

    def dispose(self):
        GL.glDeleteBuffers(1, as_uint32_array(self.__id))
        self.__id = -1

    def __del__(self):
        if self.__id != -1:
            self.dispose()


class VertexBuffer(Buffer):
    def __init__(self):
        super(VertexBuffer, self).__init__(GL.GL_ARRAY_BUFFER)

    def set_data(self,  data):
        GL.glNamedBufferData(self.id, len(data) * data.itemsize, data, GL.GL_STATIC_DRAW)


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

    def bind_vertex_buffer(self, vbo, binding, attribute, element_count, attr_type, stride):
        GL.glEnableVertexArrayAttrib(self.__id, attribute)
        GL.glVertexArrayAttribFormat(self.__id, attribute, element_count, attr_type, False, 0)
        GL.glVertexArrayAttribBinding(self.__id, attribute, binding)
        GL.glVertexArrayVertexBuffer(self.__id, binding, vbo.id, 0, stride)

    def bind_index_buffer(self, ibo):
        GL.glVertexArrayElementBuffer(self.__id, ibo.id)

    def __del__(self):
        if self.__id != -1:
            self.dispose()


class IndexBuffer(Buffer):
    def __init__(self):
        super(IndexBuffer, self).__init__(GL.GL_ELEMENT_ARRAY_BUFFER)

    def set_indices(self, indices):
        GL.glNamedBufferData(self.id, len(indices) * indices.itemsize, indices, GL.GL_STATIC_DRAW)
