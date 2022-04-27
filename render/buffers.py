import numpy as np
import numpy.typing as npt
from OpenGL import GL as GL

from helpers import as_uint32_array
from render.unmanaged import UnmanagedResource


class Buffer(UnmanagedResource):
    def __init__(self, target: GL.Constant):
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


class VertexBuffer(Buffer):
    def __init__(self):
        super(VertexBuffer, self).__init__(GL.GL_ARRAY_BUFFER)

    def set_data(self, size: int, data, usage: GL.Constant = GL.GL_STATIC_DRAW):
        GL.glNamedBufferData(self.id, size, data, usage)


class IndexBuffer(Buffer):
    def __init__(self):
        super(IndexBuffer, self).__init__(GL.GL_ELEMENT_ARRAY_BUFFER)

    def set_indices(self, indices: npt.NDArray[np.uint], usage: GL.Constant = GL.GL_STATIC_DRAW):
        GL.glNamedBufferData(self.id, len(indices) * indices.itemsize, indices, usage)
