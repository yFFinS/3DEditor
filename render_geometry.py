import OpenGL.GL as GL
import glm
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


class SceneLine(SceneObject):
    def __init__(self, line):
        super(SceneLine, self).__init__()

        self.line = line
        self.mesh = Mesh()
        self.render_mode = GL.GL_LINES

        self.update_mesh(self.line.point1.position, self.line.point2.position)

    def get_render_mat(self, camera):
        return camera.get_proj_mat() * camera.get_view_mat()

    def update_mesh(self, p1, p2):
        self.mesh.set_positions(np.array([p1, p2]))
        self.mesh.set_indices(to_uint32_array([0, 1]))
        self.mesh.set_colors(np.array([glm.vec4(0, 0, 0, 1), glm.vec4(0, 0, 0, 1)]))
        
    def render(self, camera):
        p1, p2 = self.line.get_pivot_points()

        # if almost_equal_vec(p1, p2):
        #     return
        #
        # intersections = intersect_line_frustum(p1, p2, camera.get_frustum_edges())
        # print(intersections)
        # if len(intersections) != 2:
        #     return
        #
        # self.update_mesh(*intersections)

        # Умом
        dir_v = self.line.get_directional_vector()
        self.update_mesh(p1 + 10000 * dir_v, p2 - 10000 * dir_v)

        super(SceneLine, self).render(camera)


class ScenePlane(SceneObject):
    def __init__(self, plane):
        super(ScenePlane, self).__init__()
        self.plane = plane
        self.mesh = Mesh()
        self.render_mode = GL.GL_TRIANGLES

        self.__render_mat = None

        self.update_mesh(self.plane.point1.xyz, self.plane.point2.xyz, self.plane.point3.xyz)
        self.mesh.set_indices(to_uint32_array([0, 1, 2]))
        self.mesh.set_colors(np.array([glm.vec4(0, 0, 0, 1), glm.vec4(0, 0, 0, 1)]))

    def update_mesh(self, p1, p2, p3):
        self.mesh.set_positions(np.array([p1, p2, p3]))

    def get_render_mat(self, camera):
        return self.__render_mat

    def render(self, camera):
        p1, p2, p3 = self.plane.get_pivot_points()
        camera.to_screen_space(p1)
        mvp = camera.get_mvp(self.get_model_mat())
        sp1 = mvp * p1
        sp2 = mvp * p2
        sp3 = mvp * p3
        dir_v = self.line.get_directional_vector()
        sp1 += dir_v * 10

        super(ScenePlane, self).render(camera)