import OpenGL.GL as GL

from core.Base_geometry_objects import *
from render.mesh import Mesh
from scene.camera import Camera
from scene.scene_object import SceneObject, RawSceneObject
from core.helpers import *

SELECT_POINT = 1 << 0
SELECT_LINE = 1 << 1
SELECT_PLANE = 1 << 2
SELECT_EDGE = 1 << 3
SELECT_FACE = 1 << 4


class ScenePoint(SceneObject):
    USE_SHARED_MESH = True
    __shared_mesh = None

    def __init__(self, point: Point):
        super(ScenePoint, self).__init__(point)

        self.point = point
        self.transform.translation = point.pos
        self.render_mode = GL.GL_POINTS
        self.render_layer = 1
        self.selection_mask = SELECT_POINT

        if ScenePoint.USE_SHARED_MESH:
            if ScenePoint.__shared_mesh is None:
                ScenePoint.__shared_mesh = ScenePoint.__create_mesh()
            self.mesh = ScenePoint.__shared_mesh
        else:
            self.mesh = self.__create_mesh()

    @classmethod
    def from_pos(cls, pos: glm.vec3) -> 'ScenePoint':
        return ScenePoint(Point(pos))

    @staticmethod
    def __create_mesh():
        mesh = Mesh()
        mesh.set_positions(np.array([glm.vec3(0, 0, 0)]))
        mesh.set_colors(np.array([glm.vec4(0, 0, 0, 1)]))
        return mesh

    def update_hierarchy_position(self, pos: glm.vec3, ignored: set['SceneObject']):
        self.point.pos = pos
        self.transform.translation = pos
        for child in self.children:
            if child not in ignored:
                child.on_parent_position_updated(self)

    def get_selection_weight(self, camera: Camera, screen_pos: glm.vec2) -> float:
        spos = camera.world_to_screen(self.transform.translation)
        dist = glm.distance(screen_pos, spos)

        max_dist = 20
        if dist > max_dist:
            return np.nan
        return 1 - 0.8 * dist / max_dist


class SceneLine(SceneObject):
    def __init__(self, line: BaseLine, *parents: SceneObject):
        super(SceneLine, self).__init__(line, *parents)

        self.line = line
        self.render_mode = GL.GL_LINES
        self.render_layer = 1
        self.selection_mask = SELECT_LINE

        self.mesh = Mesh()
        self.update_mesh()
        self.mesh.set_colors(np.array([glm.vec4(0, 0, 0, 1)] * 2))

    @classmethod
    def by_point_and_line(cls, scene_point: ScenePoint, scene_line: 'SceneLine') -> 'SceneLine':
        line = LineByPointAndLine(scene_point.point, scene_line.line)
        self = cls(line, scene_point, scene_line)
        return self

    @classmethod
    def by_two_points(cls, scene_point1: ScenePoint, scene_point2: ScenePoint) -> 'SceneLine':
        line = LineBy2Points(scene_point1.point, scene_point2.point)
        self = cls(line, scene_point1, scene_point2)
        return self

    def get_render_mat(self, camera: Camera):
        return camera.proj_view_matrix

    def update_hierarchy_position(self, pos: glm.vec3):
        self.transform.translation = pos

    def update_mesh(self):
        # TODO: Умом
        dir_v = self.line.get_directional_vector()
        p1, p2 = self.line.get_pivot_points()
        self.mesh.set_positions(np.array([p1 + 1000 * dir_v, p2 - 1000 * dir_v]))

    def prepare_render(self, camera: Camera):
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

        self.update_mesh()
        super(SceneLine, self).prepare_render(camera)


class ScenePlane(SceneObject):
    COLOR = glm.vec4(137 / 256, 143 / 256, 141 / 256, 0.7)

    def __init__(self, plane: BasePlane, *parents: SceneObject):
        super(ScenePlane, self).__init__(plane, *parents)

        self.plane = plane
        self.render_mode = GL.GL_TRIANGLES
        self.render_layer = 1
        self.selection_mask = SELECT_PLANE

        self.mesh = Mesh()
        self.__update_local_position()
        self.mesh.set_colors(np.array([ScenePlane.COLOR] * self.mesh.get_vertex_count()))

    @classmethod
    def by_point_and_plane(cls, scene_point: ScenePoint, scene_plane: 'ScenePlane') -> 'ScenePlane':
        plane = PlaneByPointAndPlane(scene_point.point, scene_plane.plane)
        self = cls(plane, scene_point, scene_plane)
        return self

    @classmethod
    def by_three_points(cls, scene_point1: ScenePoint, scene_point2: ScenePoint,
                        scene_point3: ScenePoint) -> 'ScenePlane':
        plane = PlaneBy3Points(scene_point1.point, scene_point2.point, scene_point3.point)
        self = cls(plane, scene_point1, scene_point2, scene_point3)
        return self

    def __update_local_position(self):
        p1, p2, p3 = self.plane.get_pivot_points()
        center = (p1 + p2 + p3) / 2
        self.transform.translation = center
        self.mesh.set_positions(np.array([p1 - center, p2 - center, p3 - center]) * 10)

    def update_hierarchy_position(self, pos: glm.vec3, ignored: set['SceneObject']):
        move = pos - self.transform.translation
        self.transform.translation = pos

        p1, p2, p3 = [parent for parent in self.parents if isinstance(parent, ScenePoint)]
        ignored.add(self)
        if p1 not in ignored:
            p1.update_hierarchy_position(p1.transform.translation + move, ignored)
        if p2 not in ignored:
            p2.update_hierarchy_position(p2.transform.translation + move, ignored)
        if p3 not in ignored:
            p3.update_hierarchy_position(p3.transform.translation + move, ignored)

    def on_parent_position_updated(self, parent: 'SceneObject'):
        self.__update_local_position()


class SceneEdge(SceneObject):
    def __init__(self, segment: Segment, *parents: SceneObject):
        super(SceneEdge, self).__init__(segment, *parents)

        self.edge = segment
        self.render_mode = GL.GL_LINES
        self.render_layer = 1
        self.selection_mask = SELECT_EDGE

        self.mesh = Mesh()
        self.__update_local_position()
        self.mesh.set_colors(np.array([glm.vec4(0, 0, 0, 1)] * self.mesh.get_vertex_count()))

    @classmethod
    def by_two_points(cls, scene_point1: ScenePoint, scene_point2: ScenePoint) -> 'SceneEdge':
        edge = Segment(scene_point1.point, scene_point2.point)
        self = cls(edge, scene_point1, scene_point2)
        return self

    def __update_local_position(self):
        p1, p2 = self.edge.point1, self.edge.point2
        self.transform.translation = (p1.pos + p2.pos) / 2
        half = (p2.pos - p1.pos) / 2
        self.mesh.set_positions(np.array([-half, half]))

    def update_hierarchy_position(self, pos: glm.vec3, ignored: set['SceneObject']):
        move = pos - self.transform.translation
        self.transform.translation = pos

        p1, p2 = list(self.parents)
        ignored.add(self)
        if p1 not in ignored:
            p1.update_hierarchy_position(p1.transform.translation + move, ignored)
        if p2 not in ignored:
            p2.update_hierarchy_position(p2.transform.translation + move, ignored)

        for child in self.children:
            if child not in ignored:
                child.on_parent_position_updated(self)

    def on_parent_position_updated(self, parent: 'SceneObject'):
        self.__update_local_position()


class SceneFace(SceneObject):
    COLOR = glm.vec4(137 / 256, 143 / 256, 141 / 256, 1)

    def __init__(self, triangle: Triangle, *parents: SceneObject):
        super(SceneFace, self).__init__(triangle, *parents)

        self.face = triangle
        self.render_mode = GL.GL_TRIANGLES
        self.render_layer = 1
        self.selection_mask = SELECT_FACE

        self.mesh = Mesh()
        self.__update_local_position()
        self.mesh.set_colors(np.array([SceneFace.COLOR] * self.mesh.get_vertex_count()))

    @classmethod
    def by_three_points(cls, scene_point1: ScenePoint, scene_point2: ScenePoint,
                        scene_point3: ScenePoint) -> 'SceneFace':
        face = Triangle(scene_point1.point, scene_point2.point, scene_point3.point)
        self = cls(face, scene_point1, scene_point2, scene_point3)
        return self

    def __update_local_position(self):
        p1, p2, p3 = self.face.point1, self.face.point2, self.face.point3
        center = (p1.pos + p2.pos + p3.pos) / 2
        self.transform.translation = center
        self.mesh.set_positions(np.array([p1.pos - center, p2.pos - center, p3.pos - center]))

    def update_hierarchy_position(self, pos: glm.vec3, ignored: set['SceneObject']):
        move = pos - self.transform.translation
        self.transform.translation = pos

        p1, p2, p3 = [parent for parent in self.parents if isinstance(parent, ScenePoint)]
        ignored.add(self)
        if p1 not in ignored:
            p1.update_hierarchy_position(p1.transform.translation + move, ignored)
        if p2 not in ignored:
            p2.update_hierarchy_position(p2.transform.translation + move, ignored)
        if p3 not in ignored:
            p3.update_hierarchy_position(p3.transform.translation + move, ignored)

    def on_parent_position_updated(self, parent: 'SceneObject'):
        self.__update_local_position()


class SceneCoordAxis(RawSceneObject):
    AXIS_LENGTH = 5
    X_COLOR = glm.vec4(1, 0, 0, 1)
    Y_COLOR = glm.vec4(0, 1, 0, 1)
    Z_COLOR = glm.vec4(0, 0, 1, 1)
    NEG_COLOR_FACTOR = 150
    NEG_X_COLOR = glm.vec4(1, NEG_COLOR_FACTOR / 256, NEG_COLOR_FACTOR / 256, 1)
    NEG_Y_COLOR = glm.vec4(NEG_COLOR_FACTOR / 256, 1, NEG_COLOR_FACTOR / 256, 1)
    NEG_Z_COLOR = glm.vec4(NEG_COLOR_FACTOR / 256, NEG_COLOR_FACTOR / 256, 1, 1)

    def __init__(self):
        super(SceneCoordAxis, self).__init__()

        self.render_mode = GL.GL_LINES
        self.render_layer = -1
        self.transform.scale = glm.vec3(2)

        self.populate_mesh()

    def populate_mesh(self):
        axis_length = SceneCoordAxis.AXIS_LENGTH
        positions = np.array([
            glm.vec3(0, 0, 0),
            glm.vec3(axis_length, 0, 0),
            glm.vec3(0, 0, 0),
            glm.vec3(0, axis_length, 0),
            glm.vec3(0, 0, 0),
            glm.vec3(0, 0, axis_length),
            glm.vec3(0, 0, 0),
            glm.vec3(-axis_length, 0, 0),
            glm.vec3(0, 0, 0),
            glm.vec3(0, -axis_length, 0),
            glm.vec3(0, 0, 0),
            glm.vec3(0, 0, -axis_length),
        ])

        self.mesh = Mesh()
        self.mesh.set_positions(positions)
        self.mesh.set_colors(np.array([SceneCoordAxis.X_COLOR, SceneCoordAxis.X_COLOR,
                                       SceneCoordAxis.Y_COLOR, SceneCoordAxis.Y_COLOR,
                                       SceneCoordAxis.Z_COLOR, SceneCoordAxis.Z_COLOR,
                                       SceneCoordAxis.NEG_X_COLOR, SceneCoordAxis.NEG_X_COLOR,
                                       SceneCoordAxis.NEG_Y_COLOR, SceneCoordAxis.NEG_Y_COLOR,
                                       SceneCoordAxis.NEG_Z_COLOR, SceneCoordAxis.NEG_Z_COLOR]))

    def adjust_to_camera(self, camera: Camera):
        camera_pos = camera.translation
        distance = glm.distance(camera_pos, self.transform.translation)
        self.transform.scale = glm.vec3(distance)

    def prepare_render(self, camera: Camera):
        self.adjust_to_camera(camera)

        GL.glLineWidth(2)
        GL.glDepthFunc(GL.GL_ALWAYS)

    def render_completed(self, camera: Camera):
        GL.glDepthFunc(GL.GL_LEQUAL)


class SceneGrid(RawSceneObject):
    MIN_CELL_SIZE = 4
    CELL_SIZE_STEP = 10
    CELL_COUNT = 10
    GRID_COLOR = glm.vec4(97 / 256, 96 / 256, 102 / 256, 1)

    def __init__(self):
        super(SceneGrid, self).__init__()

        self.render_mode = GL.GL_LINES
        self.render_layer = -2
        self.cell_size = SceneGrid.MIN_CELL_SIZE
        self.transform.scale = glm.vec3(self.cell_size)
        self.populate_mesh()

    def populate_mesh(self):
        half_row_count = SceneGrid.CELL_COUNT

        positions = []
        for y in range(-half_row_count - 1, half_row_count + 1):
            for x in range(-half_row_count - 1, half_row_count + 1):
                pos = glm.vec3(x, 0, y)
                positions.append(pos)
        indices = []

        row_size = 2 * half_row_count + 2
        for y in range(row_size):
            for x in range(row_size):
                if y < row_size - 1:
                    indices.append(x + y * row_size)
                    indices.append(x + (y + 1) * row_size)
                if x < row_size - 1:
                    indices.append(y * row_size + x)
                    indices.append(y * row_size + x + 1)
        self.mesh = Mesh()
        self.mesh.set_positions(np.array(positions))
        self.mesh.set_indices(np.array(indices))
        self.mesh.set_colors(np.array([SceneGrid.GRID_COLOR] * len(positions)))

    def adjust_to_camera(self, camera: Camera):
        camera_pos = camera.translation
        step = SceneGrid.CELL_SIZE_STEP
        self.cell_size = max(abs(camera_pos.y) // step * step, SceneGrid.MIN_CELL_SIZE)
        self.transform.scale = glm.vec3(self.cell_size)

        cam_x, cam_z = camera_pos.x, camera_pos.z
        pos = self.transform.translation
        pos.x = cam_x // self.cell_size * self.cell_size + self.cell_size
        pos.z = cam_z // self.cell_size * self.cell_size + self.cell_size
        self.transform.translation = pos

    def prepare_render(self, camera: Camera):
        self.adjust_to_camera(camera)

        GL.glLineWidth(1)
        super(SceneGrid, self).prepare_render(camera)
