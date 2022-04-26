import OpenGL.GL as GL
from OpenGL.GL.shaders import compileShader, compileProgram
import glm
from helpers import as_uint32_array, empty_uint32_array, empty_float32_array


class UnmanagedResource:
    def dispose(self):
        pass


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


class VertexBuffer(Buffer):
    def __init__(self, usage=GL.GL_STATIC_DRAW):
        self.usage = usage
        super(VertexBuffer, self).__init__(GL.GL_ARRAY_BUFFER)

    def set_data(self, size, data):
        GL.glNamedBufferData(self.id, size, data, self.usage)


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


class IndexBuffer(Buffer):
    def __init__(self):
        super(IndexBuffer, self).__init__(GL.GL_ELEMENT_ARRAY_BUFFER)

    def set_indices(self, indices):
        GL.glNamedBufferData(self.id, len(indices) * indices.itemsize, indices, GL.GL_STATIC_DRAW)


class Mesh:
    def __init__(self):
        self.__vba = VertexArray()

        self.__vbo_positions = VertexBuffer(GL.GL_STREAM_DRAW)
        self.__vbo_colors = VertexBuffer()
        self.__ibo = IndexBuffer()

        self.__vba.bind_vertex_buffer(self.__vbo_positions, 0, 0, 3, GL.GL_FLOAT, 12)
        self.__vba.bind_vertex_buffer(self.__vbo_colors, 1, 1, 4, GL.GL_FLOAT, 16)
        self.__vba.bind_index_buffer(self.__ibo)

        self.__indices = empty_uint32_array()
        self.__positions = empty_float32_array()
        self.__colors = empty_float32_array()

    def set_positions(self, positions):
        self.__vbo_positions.set_data(glm.sizeof(glm.vec3) * len(positions), positions)
        self.__positions = positions.copy()

    def set_colors(self, colors):
        self.__vbo_colors.set_data(glm.sizeof(glm.vec4) * len(colors), colors)
        self.__colors = colors.copy()

    def set_indices(self, indices):
        self.__ibo.set_indices(indices)
        self.__indices = indices.copy()

    def get_positions(self):
        return self.__positions.copy()

    def get_colors(self):
        return self.__colors.copy()

    def get_indices(self):
        return self.__indices.copy()

    def get_index_count(self):
        return len(self.__indices)

    def get_vertex_count(self):
        return len(self.__positions)

    def bind_vba(self):
        self.__vba.bind()

    def unbind_vba(self):
        self.__vba.unbind()


class ShaderProgram(UnmanagedResource):
    def __init__(self, vertex, fragment):
        try:
            with open(vertex) as f:
                vertex_source = f.read()
            with open(fragment) as f:
                fragment_source = f.read()
        except OSError as e:
            print(e)
            return

        self.__vertex = compileShader(vertex_source, GL.GL_VERTEX_SHADER)
        self.__fragment = compileShader(fragment_source, GL.GL_FRAGMENT_SHADER)
        self.__program = compileProgram(self.__vertex, self.__fragment)

    def use(self):
        GL.glUseProgram(self.__program)

    def set_mat4(self, name, value):
        loc = GL.glGetUniformLocation(self.__program, name)
        GL.glUniformMatrix4fv(loc, 1, False, glm.value_ptr(value))

    def set_float(self, name, value):
        loc = GL.glGetUniformLocation(self.__program, name)
        GL.glUniform1fv(loc, 1, value)

    def dispose(self):
        if self.__program == -1:
            return
        GL.glDeleteShader(self.__vertex)
        self.__vertex = -1
        GL.glDeleteShader(self.__fragment)
        self.__fragment = -1
        GL.glDeleteProgram(self.__program)
        self.__program = -1

    def __del__(self):
        self.dispose()
