import OpenGL.GL as GL
import numpy as np

from geometry import *
from scenes import SceneObject, Mesh
from helpers import *


class ScenePoint(SceneObject):
    def __init__(self, point):
        super(ScenePoint, self).__init__()

        self.translation = point.position
        self.point = point
        self.render_mode = GL.GL_POINTS
        self.mesh = Mesh()
        self.mesh.set_positions(np.array([glm.vec3(0, 0, 0)]))
        self.mesh.set_indices(as_uint32_array(0))
        self.mesh.set_colors(np.array([glm.vec4(0, 0, 0, 1)]))

    def set_position(self, x, y, z):
        self.point.position = glm.vec3(x, y, z)
        self.translation = glm.vec3(x, y, z)


class SceneLineBy2Points(SceneObject):
    def __init__(self, line):
        super(SceneLineBy2Points, self).__init__()

        self.line = line
        self.mesh = Mesh()
        self.render_mode = GL.GL_LINES

        self.update_mesh()

    def update_mesh(self):
        self.mesh.set_positions(np.array([self.line.point1.position, self.line.point2.position]))
        self.mesh.set_indices(to_uint32_array([0, 1]))
        self.mesh.set_colors(np.array([glm.vec4(0, 0, 0, 1), glm.vec4(0, 0, 0, 1)]))


class SceneLineByPointAndLine(SceneObject):
    def __init__(self, line):
        super(SceneLineByPointAndLine, self).__init__()

        self.line = line
        self.mesh = Mesh()
        self.render_mode = GL.GL_LINES

        self.update_mesh()

    def update_mesh(self):
        self.mesh.set_positions(np.array([self.line.point1.position, self.line.point2.position]))
        self.mesh.set_indices(to_uint32_array([0, 1]))
        self.mesh.set_colors(np.array([glm.vec4(0, 0, 0, 1), glm.vec4(0, 0, 0, 1)]))
        
    def render(self, camera):
        super(SceneLineByPointAndLine, self).render(camera)