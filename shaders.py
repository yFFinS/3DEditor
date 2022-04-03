import OpenGL.GL as GL
from OpenGL.GL.shaders import compileShader, compileProgram
from common import UnmanagedResource


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

    def dispose(self):
        GL.glDeleteShader(self.__vertex)
        self.__vertex = -1
        GL.glDeleteShader(self.__fragment)
        self.__fragment = -1
        GL.glDeleteProgram(self.__program)
        self.__program = -1

    def __del__(self):
        if self.__program != -1:
            self.dispose()
