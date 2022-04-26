import OpenGL.GL as GL
import math

import glm

from geometry import *
from scene import SceneObject, Mesh
from helpers import *


SELECT_POINT = 1 << 0
SELECT_LINE = 1 << 1
SELECT_PLANE = 1 << 2
SCALING_FACTOR = 2


class ScenePoint(SceneObject):
    def __init__(self, point):
        super(ScenePoint, self).__init__()

        self.translation = point.position
        self.point = point
        self.render_mode = GL.GL_POINTS
        self.render_layer = 4

        self.mesh.set_positions(np.array([glm.vec3(0, 0, 0)]))
        self.mesh.set_indices(as_uint32_array(0))
        self.mesh.set_colors(np.array([glm.vec4(0, 0, 0, 1)]))

    def get_selection_mask(self):
        return SELECT_POINT

    def set_position(self, x, y, z):
        self.point.position = glm.vec3(x, y, z)
        super(ScenePoint, self).set_position(x, y, z)

    def get_selection_weight(self, camera, x, y):
        pos = glm.vec2(x, y)
        spos = camera.world_to_screen_space(self.translation)
        dist = glm.distance(pos, spos)

        max_dist = 20
        if dist > max_dist:
            return None
        return 1 - 0.8 * dist / max_dist


class SceneLine(SceneObject):
    def __init__(self, line):
        super(SceneLine, self).__init__()

        self.line = line
        self.render_mode = GL.GL_LINES
        self.render_layer = 3

        self.update_mesh(self.line.point1.xyz, self.line.point2.xyz)

    def get_selection_mask(self):
        return SELECT_LINE

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

        # TODO: Умом
        dir_v = self.line.get_directional_vector()
        self.update_mesh(p1 + 1000 * dir_v, p2 - 1000 * dir_v)

        GL.glLineWidth(1)
        super(SceneLine, self).render(camera)


class ScenePlane(SceneObject):
    def __init__(self, plane):
        super(ScenePlane, self).__init__()

        self.plane = plane
        self.render_mode = GL.GL_TRIANGLES
        self.render_layer = 2

        self.__render_mat = None

        self.update_mesh(self.plane.point1.xyz, self.plane.point2.xyz, self.plane.point3.xyz)
        self.mesh.set_indices(to_uint32_array([0, 1, 2]))
        self.mesh.set_colors(np.array([glm.vec4(0, 0, 0, 1), glm.vec4(0, 0, 0, 1)]))

    def get_selection_mask(self):
        return SELECT_PLANE

    def update_mesh(self, p1, p2, p3):
        self.mesh.set_positions(np.array([p1, p2, p3]))

    def render(self, camera):
        super(ScenePlane, self).render(camera)


AXIS_EXTENTS = 20


class SceneCoordAxis(SceneObject):
    def __init__(self):
        super(SceneCoordAxis, self).__init__()

        self.render_mode = GL.GL_LINES
        self.render_layer = -1
        self.scale = glm.vec3(2)

        self.populate_mesh()

    def populate_mesh(self):
        axis_line_color = glm.vec4(16 / 256, 79 / 256, 196 / 256, 1)

        positions = np.array([
                glm.vec3(-AXIS_EXTENTS, 0, 0),
                glm.vec3(AXIS_EXTENTS, 0, 0),
                glm.vec3(0, -AXIS_EXTENTS, 0),
                glm.vec3(0, AXIS_EXTENTS, 0),
                glm.vec3(0, 0, -AXIS_EXTENTS),
                glm.vec3(0, 0, AXIS_EXTENTS)
            ])

        self.mesh.set_positions(positions)
        self.mesh.set_indices(np.array(range(len(positions))))
        self.mesh.set_colors(np.array([axis_line_color for _ in range(len(positions))]))

    def adjust_to_camera(self, camera):
        camera_pos = camera.translation
        distance = glm.distance(camera_pos, self.translation)
        scale_step = int(math.log(distance, SCALING_FACTOR))
        size = 2 + SCALING_FACTOR ** scale_step
        self.scale = glm.vec3(size)

    def render(self, camera):
        self.adjust_to_camera(camera)

        GL.glLineWidth(2)
        super(SceneCoordAxis, self).render(camera)


class SceneGrid(SceneObject):
    def __init__(self):
        super(SceneGrid, self).__init__()

        self.render_mode = GL.GL_LINES
        self.render_layer = -2
        self.cell_size = 2
        self.scale = glm.vec3(self.cell_size)

        self.populate_mesh()

    def populate_mesh(self):
        half_row_count = AXIS_EXTENTS * 2
        grid_color = glm.vec4(0.7, 0.1, 0.2, 1)

        positions = []
        for y in range(-half_row_count, half_row_count):
            for x in range(-half_row_count, half_row_count):
                pos = glm.vec3(x, 0, y) * 0.5
                positions.append(pos)
        indices = []

        row_size = 2 * half_row_count
        for y in range(row_size):
            for x in range(row_size):
                if y < row_size - 1:
                    indices.append(x + y * row_size)
                    indices.append(x + (y + 1) * row_size)
                if x < row_size - 1:
                    indices.append(y * row_size + x)
                    indices.append(y * row_size + x + 1)

        self.mesh.set_positions(np.array(positions))
        self.mesh.set_indices(np.array(indices))
        self.mesh.set_colors(np.array([grid_color for _ in range(len(positions))]))

    def adjust_to_camera(self, camera):
        camera_pos = camera.translation
        scale_step = int(math.log(abs(camera_pos.y), SCALING_FACTOR))
        self.cell_size = 2 + SCALING_FACTOR ** scale_step
        self.scale = glm.vec3(self.cell_size)

        cam_x, cam_z = camera_pos.x, camera_pos.z
        self.translation.x = cam_x // self.cell_size * self.cell_size
        self.translation.z = cam_z // self.cell_size * self.cell_size

    def render(self, camera):
        self.adjust_to_camera(camera)

        GL.glLineWidth(0.3)
        super(SceneGrid, self).render(camera)
