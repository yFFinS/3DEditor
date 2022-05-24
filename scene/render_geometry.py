import OpenGL.GL as GL
import glm

import profiling.profiler
from core.Base_geometry_objects import *
from render.mesh import Mesh
from render.shared_vbo import SharedMesh
from scene.camera import Camera
from scene.scene_object import SceneObject, RawSceneObject
from core.helpers import *

SELECT_POINT = 1 << 0
SELECT_LINE = 1 << 1
SELECT_PLANE = 1 << 2
SELECT_EDGE = 1 << 3
SELECT_FACE = 1 << 4


class ScenePoint(SceneObject):
    SEL_COLOR = glm.vec4(0.4, 0.4, 1, 1)

    def __init__(self, point: Point):
        super(ScenePoint, self).__init__(point)

        self.point = point
        self.transform.translation = point.pos
        self.render_mode = GL.GL_POINTS
        self.render_layer = 1
        self.selection_mask = SELECT_POINT

        self.mesh = SharedMesh.request_mesh(1, self.render_mode)
        self.__update_mesh()
        self.set_selected(False)

    def on_delete(self):
        self.mesh.clear()
        super(ScenePoint, self).on_delete()

    def set_selected(self, value: bool):
        self.mesh.set_colors(
            np.array([ScenePoint.SEL_COLOR
                      if value else glm.vec4(0, 0, 0, 1)]))

    @classmethod
    def by_pos(cls, pos: glm.vec3) -> 'ScenePoint':
        return ScenePoint(Point(pos))

    @profiling.profiler.profile
    def __update_mesh(self):
        self.mesh.set_positions(np.array([self.point.pos]))

    def update_hierarchy_position(self, pos: glm.vec3,
                                  ignored: set['SceneObject']):
        self.point.pos = pos
        self.transform.translation = pos
        self.__update_mesh()

        for child in self.children:
            if child not in ignored:
                child.on_parent_position_updated(self)

    def get_selection_weight(self, camera: Camera,
                             screen_pos: glm.vec2) -> float:
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
        self.__update_local_positions()
        self.mesh.set_colors(np.array([glm.vec4(0, 0, 0, 1)] * 2))

    @classmethod
    def by_point_and_line(cls, scene_point: ScenePoint,
                          scene_line: 'SceneLine') -> 'SceneLine':
        line = LineByPointAndLine(scene_point.point, scene_line.line)
        self = cls(line, scene_point, scene_line)
        return self

    @classmethod
    def by_two_points(cls, scene_point1: ScenePoint,
                      scene_point2: ScenePoint) -> 'SceneLine':
        line = LineBy2Points(scene_point1.point, scene_point2.point)
        self = cls(line, scene_point1, scene_point2)
        return self

    def update_hierarchy_position(self, pos: glm.vec3,
                                  ignored: set['SceneObject']):
        move = pos - self.transform.translation
        self.transform.translation = pos

        ignored.add(self)
        for point in (parent for parent in self.parents if
                      parent not in ignored):
            point.update_hierarchy_position(point.transform.translation + move,
                                            ignored)

    def prepare_render(self, camera: Camera):
        dist = glm.distance(self.transform.translation, camera.translation)
        self.transform.scale = glm.vec3(max(dist / 1.5, 1))
        super(SceneLine, self).prepare_render(camera)

    def __update_local_positions(self):
        p1, p2 = self.line.get_pivot_points()
        directional_vec = self.line.get_directional_vector()
        center = (p1 + p2) / 2
        self.transform.translation = center
        additional_distance = 1
        self.mesh.set_positions(np.array([additional_distance * directional_vec,
                                          -additional_distance * directional_vec]))

    def on_parent_position_updated(self, parent: 'SceneObject'):
        self.__update_local_positions()

    def get_selection_weight(self, camera: Camera,
                             click_pos: glm.vec2) -> float:

        pivots = self.line.get_pivot_points()
        transformed_pivots = [camera.world_to_screen(point) for point in pivots]
        distance = point_to_line_distance(click_pos, *transformed_pivots)
        max_dist = 20
        factor = 0.8
        if distance > max_dist:
            return np.nan
        return (1 - distance / max_dist) * factor


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
        self.mesh.set_indices(np.array([0, 1, 2, 0, 3, 2]))
        self.mesh.set_colors(
            np.array([ScenePlane.COLOR] * self.mesh.get_vertex_count()))

    @classmethod
    def by_point_and_plane(cls, scene_point: ScenePoint,
                           scene_plane: 'ScenePlane') -> 'ScenePlane':
        plane = PlaneByPointAndPlane(scene_point.point, scene_plane.plane)
        self = cls(plane, scene_point, scene_plane)
        return self

    @classmethod
    def by_three_points(cls, scene_point1: ScenePoint, scene_point2: ScenePoint,
                        scene_point3: ScenePoint) -> 'ScenePlane':
        plane = PlaneBy3Points(scene_point1.point, scene_point2.point,
                               scene_point3.point)
        self = cls(plane, scene_point1, scene_point2, scene_point3)
        return self

    @classmethod
    def by_point_and_line(cls, scene_point: ScenePoint,
                          scene_line: SceneLine) -> 'ScenePlane':
        plane = PlaneByPointAndLine(scene_point.point, scene_line.line)
        self = cls(plane, scene_point, scene_line)
        return self

    @classmethod
    def by_point_and_segment(cls, scene_point: ScenePoint,
                             scene_segment: 'SceneEdge') -> 'ScenePlane':
        plane = PlaneByPointAndSegment(scene_point.point, scene_segment.edge)
        self = cls(plane, scene_point, scene_segment)
        return self

    def __update_local_position(self):
        p1, p2, p3 = self.plane.get_pivot_points()
        center = (p1 + p2 + p3) / 3
        self.transform.translation = center
        square_points = self.__get_square_points()
        self.mesh.set_positions(np.array(square_points))

    def __get_square_points(self):
        p1, p2, p3 = self.plane.get_pivot_points()
        center = (p1 + p2 + p3) / 3
        norm = self.plane.get_normal()
        op1 = glm.normalize(p1 - center) * 1000
        op2 = glm.normalize(glm.cross(norm, op1)) * 1000
        return [op1, op2, -op1, -op2]

    def update_hierarchy_position(self, pos: glm.vec3,
                                  ignored: set['SceneObject']):
        move = pos - self.transform.translation
        self.transform.translation = pos

        ignored.add(self)
        point_parents = [parent for parent in self.parents if
                         isinstance(parent, ScenePoint)]
        for i in range(min(len(point_parents), 3)):
            point = point_parents[i]
            point.update_hierarchy_position(point.transform.translation + move,
                                            ignored)

    def get_selection_weight(self, camera: Camera,
                             click_pos: glm.vec2) -> float:
        square_points = self.__get_square_points()
        model = self.transform.model_matrix
        transformed_points = [model * point for point in square_points]
        origin = camera.translation
        direction = camera.screen_to_world(click_pos)

        intersection_distance1 = ray_triangle_intersection_distance(
            origin, direction,
            *[glm.vec3(point) for point in transformed_points[:3]])
        intersection_distance2 = ray_triangle_intersection_distance(
            origin, direction,
            *[glm.vec3(point) for point in transformed_points[1:]])

        if glm.isnan(intersection_distance1) and glm.isnan(
                intersection_distance2):
            return np.nan

        distance = intersection_distance1 if not glm.isnan(
            intersection_distance1) else intersection_distance2
        mapped = glm.atan(distance) / (glm.pi() / 2) * 0.8
        return 1 - mapped

    def on_parent_position_updated(self, parent: 'SceneObject'):
        self.__update_local_position()
        for child in self.children:
            if isinstance(child, ScenePlane):
                child.on_parent_position_updated(self)

    def prepare_render(self, camera: Camera):
        dist = glm.distance(self.transform.translation, camera.translation)
        self.transform.scale = glm.vec3(max(dist / 1.5, 1))
        super(ScenePlane, self).prepare_render(camera)


class SceneEdge(SceneObject):
    SEL_COLOR = glm.vec4(0.55, 0.55, 1, 1)

    def __init__(self, segment: Segment, *parents: SceneObject):
        super(SceneEdge, self).__init__(segment, *parents)

        self.edge = segment
        self.render_mode = GL.GL_LINES
        self.render_layer = 1
        self.selection_mask = SELECT_EDGE

        self.mesh = SharedMesh.request_mesh(2, self.render_mode)
        self.__update_local_position()
        self.set_selected(False)

    def on_delete(self):
        self.mesh.clear()
        super(SceneEdge, self).on_delete()

    def set_selected(self, value: bool):
        self.mesh.set_colors(np.array(
            [SceneEdge.SEL_COLOR if value else glm.vec4(0, 0, 0, 1)] * 2))

    @classmethod
    def by_two_points(cls, scene_point1: ScenePoint,
                      scene_point2: ScenePoint) -> 'SceneEdge':
        edge = Segment(scene_point1.point, scene_point2.point)
        self = cls(edge, scene_point1, scene_point2)
        return self

    def __update_local_position(self):
        p1, p2 = self.edge.point1, self.edge.point2
        self.transform.translation = (p1.pos + p2.pos) / 2
        self.__update_mesh()

    @profiling.profiler.profile
    def __update_mesh(self):
        p1, p2 = self.edge.point1, self.edge.point2
        self.mesh.set_positions(np.array([p1.pos, p2.pos]))

    def update_hierarchy_position(self, pos: glm.vec3,
                                  ignored: set['SceneObject']):
        move = pos - self.transform.translation
        self.transform.translation = pos

        ignored.add(self)
        for point in (point for point in self.parents if point not in ignored):
            point.update_hierarchy_position(point.transform.translation + move,
                                            ignored)

        self.__update_mesh()

        for child in (child for child in self.children if child not in ignored):
            child.on_parent_position_updated(self)

    def on_parent_position_updated(self, parent: 'SceneObject'):
        self.__update_local_position()

    def get_selection_weight(self, camera: Camera,
                             click_pos: glm.vec2) -> float:
        pivots = self.edge.get_points()
        transformed_pivots = [camera.world_to_screen(point) for point in pivots]
        distance = point_to_segment_distance(click_pos, *transformed_pivots)
        max_dist = 20
        factor = 0.8
        if distance > max_dist:
            return np.nan
        return (1 - distance / max_dist) * factor

    def get_closest_point(self, camera: Camera,
                          screen_pos: glm.vec2) -> glm.vec3:
        s1, s2 = self.edge.get_points()
        steps = 10
        step_dist = glm.distance(s1, s2) / (steps + 1)
        step_dir = glm.normalize(s2 - s1)

        closest = None
        closest_dist = 10 ** 18
        for step in range(1, steps + 1):
            p = s1 + step * step_dist * step_dir
            sp = camera.world_to_screen(p)
            dist = glm.distance2(sp, screen_pos)
            if dist < closest_dist:
                closest = p
                closest_dist = dist

        return closest

        # s1, s2 = camera.world_to_screen(self.edge.point1.pos), \
        #          camera.world_to_screen(self.edge.point2.pos)
        # cp2 = closest_point_on_segment(screen_pos, s1, s2)
        # ray_dir = camera.screen_to_world(cp2)
        # ray_orig = camera.translation
        # intersection = line_line_intersection(
        #     ray_orig, ray_orig + ray_dir, self.edge.point1.pos,
        #     self.edge.point2.pos)
        # return intersection


class SceneFace(SceneObject):
    COLOR = glm.vec4(137 / 256, 143 / 256, 141 / 256, 1)
    SEL_COLOR = glm.vec4(0.7, 0.7, 1, 1)

    def __init__(self, triangle: Triangle, *parents: SceneObject):
        super(SceneFace, self).__init__(triangle, *parents)

        self.face = triangle
        self.render_mode = GL.GL_TRIANGLES
        self.render_layer = 1
        self.selection_mask = SELECT_FACE

        self.mesh = SharedMesh.request_mesh(3, self.render_mode)
        self.__update_local_position()
        self.set_selected(False)

    def on_delete(self):
        self.mesh.clear()
        super(SceneFace, self).on_delete()

    def set_selected(self, value: bool):
        self.mesh.set_colors(
            np.array([SceneFace.SEL_COLOR if value else SceneFace.COLOR] * 3))

    @classmethod
    def by_three_points(cls, scene_point1: ScenePoint, scene_point2: ScenePoint,
                        scene_point3: ScenePoint) -> 'SceneFace':
        face = Triangle(scene_point1.point, scene_point2.point,
                        scene_point3.point)
        self = cls(face, scene_point1, scene_point2, scene_point3)
        return self

    def __update_local_position(self):
        p1, p2, p3 = self.face.point1, self.face.point2, self.face.point3
        center = (p1.pos + p2.pos + p3.pos) / 3
        self.transform.translation = center
        self.__update_mesh()

    @profiling.profiler.profile
    def __update_mesh(self):
        p1, p2, p3 = self.face.point1, self.face.point2, self.face.point3
        self.mesh.set_positions(np.array([p1.pos, p2.pos, p3.pos]))

    def update_hierarchy_position(self, pos: glm.vec3,
                                  ignored: set['SceneObject']):
        move = pos - self.transform.translation
        self.transform.translation = pos

        ignored.add(self)
        for point in (parent for parent in self.parents if
                      isinstance(parent, ScenePoint) and parent not in ignored):
            point.update_hierarchy_position(point.transform.translation + move,
                                            ignored)

        self.__update_mesh()

    def on_parent_position_updated(self, parent: 'SceneObject'):
        self.__update_local_position()

    def get_selection_weight(self, camera: Camera,
                             click_pos: glm.vec2) -> float:
        origin = camera.translation
        direction = camera.screen_to_world(click_pos)

        intersection_distance = ray_triangle_intersection_distance(
            origin, direction, *self.face.get_points())

        if glm.isnan(intersection_distance):
            return np.nan

        mapped = glm.atan(intersection_distance) / (glm.pi() / 2) * 0.8
        return 1 - mapped


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
        self.mesh.set_colors(
            np.array([SceneCoordAxis.X_COLOR, SceneCoordAxis.X_COLOR,
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
        self.cell_size = max(abs(camera_pos.y) // step * step,
                             SceneGrid.MIN_CELL_SIZE)
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
