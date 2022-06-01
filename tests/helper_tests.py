import unittest

from PyQt5 import QtCore

from interaction.geometry_builders import *
from render.shared_vbo import MeshProvider
from scene.render_geometry import *
from scene.scene import Scene
from scene.transform import Transform


class TestMesh:
    def get_mesh(self):
        return None

    def set_positions(self, *args, **kwargs):
        pass

    def set_colors(self, *args, **kwargs):
        pass

    def set_indices(self, *args, **kwargs):
        pass

    def clear(self):
        pass

    def get_vertex_count(self):
        return 1


def create_scene():
    scene = Scene()
    camera = Camera(400, 400)
    scene.camera = camera
    return scene


def empty_mods():
    return 0


def shift_mods():
    return QtCore.Qt.ShiftModifier


class IntersectionTests(unittest.TestCase):
    def test_ray_triangle(self):
        t1 = glm.vec3(1, 0, 0)
        t2 = glm.vec3(0, 1, 0)
        t3 = glm.vec3(-1, -1, 0)
        origin = glm.vec3(0, 0.1, -5)
        direction = glm.vec3(0, 0.1, 1)
        intersection = ray_triangle_intersection_distance(
            origin, direction, t1, t2, t3)
        self.assertFalse(glm.isnan(intersection))


class TestMeshProvider(MeshProvider):
    def get_unique_mesh(self) -> Mesh:
        return TestMesh()

    def get_shared_mesh(self, vertices: int, render_mode: GL.GL_CONSTANT):
        return TestMesh()


class BuilderTests(unittest.TestCase):
    def setUp(self):
        RawSceneObject.MESH_PROVIDER = TestMeshProvider()

    def test_point_builder(self):
        scene = create_scene()
        builder = PointBuilder(scene)
        builder.process_click(glm.vec2(200, 200), glm.vec3(2, 3, 4), empty_mods())
        objects = list(scene.objects)

        self.assertTrue(len(objects) == 1)
        obj = objects[0]
        self.assertTrue(isinstance(obj, ScenePoint))
        self.assertTrue(obj.primitive.pos == glm.vec3(2, 3, 4))

    def test_line_builder_two_points(self):
        scene = create_scene()
        builder = LineBuilder(scene)
        builder.process_click(glm.vec2(200, 200), glm.vec3(1, 1, 0), empty_mods())
        builder.process_click(glm.vec2(200, 300), glm.vec3(1, 2, 0), empty_mods())
        objects = list(scene.objects)

        self.assertTrue(len(objects) == 3)

        points = [obj for obj in objects if isinstance(obj, ScenePoint)]
        lines = [obj for obj in objects if isinstance(obj, SceneLine)]

        self.assertTrue(len(points) == 2)
        self.assertTrue(len(lines) == 1)

        self.assertTrue(points[0].primitive.pos == glm.vec3(1, 1, 0))
        self.assertTrue(points[1].primitive.pos == glm.vec3(1, 2, 0))

    def test_edge_builder_by_two_points(self):
        scene = create_scene()
        builder = EdgeBuilder(scene)
        builder.process_click(glm.vec2(200, 200), glm.vec3(1, 1, 0), empty_mods())
        builder.process_click(glm.vec2(200, 300), glm.vec3(1, 2, 0), empty_mods())
        objects = list(scene.objects)

        self.assertTrue(len(objects) == 3)

        points = [obj for obj in objects if isinstance(obj, ScenePoint)]
        edges = [obj for obj in objects if isinstance(obj, SceneEdge)]

        self.assertTrue(len(points) == 2)
        self.assertTrue(len(edges) == 1)

        self.assertTrue(points[0].primitive.pos == glm.vec3(1, 1, 0))
        self.assertTrue(points[1].primitive.pos == glm.vec3(1, 2, 0))

        self.assertTrue(edges[0].edge.point1 == points[0].primitive and edges[0].edge.point2 == points[1].primitive)

    def test_plane_builder_by_three_points(self):
        scene = create_scene()
        builder = PlaneBuilder(scene)
        builder.process_click(glm.vec2(200, 200), glm.vec3(1, 1, 0), empty_mods())
        builder.process_click(glm.vec2(200, 300), glm.vec3(1, 2, 0), empty_mods())
        builder.process_click(glm.vec2(300, 300), glm.vec3(2, 2, 0), empty_mods())

        objects = list(scene.objects)

        self.assertTrue(len(objects) == 4)

        points = [obj for obj in objects if isinstance(obj, ScenePoint)]
        planes = [obj for obj in objects if isinstance(obj, ScenePlane)]

        self.assertTrue(len(points) == 3)
        self.assertTrue(len(planes) == 1)

        self.assertTrue(points[0].primitive.pos == glm.vec3(1, 1, 0))
        self.assertTrue(points[1].primitive.pos == glm.vec3(1, 2, 0))
        self.assertTrue(points[2].primitive.pos == glm.vec3(2, 2, 0))

    def test_face_builder(self):
        scene = create_scene()
        builder = FaceBuilder(scene)
        builder.process_click(glm.vec2(200, 200), glm.vec3(1, 1, 0), empty_mods())
        builder.process_click(glm.vec2(200, 300), glm.vec3(1, 2, 0), empty_mods())
        builder.process_click(glm.vec2(300, 300), glm.vec3(2, 2, 0), empty_mods())

        objects = list(scene.objects)

        self.assertTrue(len(objects) == 7)

        points = [obj for obj in objects if isinstance(obj, ScenePoint)]
        edges = [obj for obj in objects if isinstance(obj, SceneEdge)]
        faces = [obj for obj in objects if isinstance(obj, SceneFace)]

        self.assertTrue(len(points) == 3)
        self.assertTrue(len(edges) == 3)
        self.assertTrue(len(faces) == 1)

        self.assertTrue(points[0].primitive.pos == glm.vec3(1, 1, 0))
        self.assertTrue(points[1].primitive.pos == glm.vec3(1, 2, 0))
        self.assertTrue(points[2].primitive.pos == glm.vec3(2, 2, 0))

        face = faces[0].face
        p1, p2, p3 = face.point1, face.point2, face.point3
        self.assertTrue(p1 == points[0].primitive and p2 == points[1].primitive and p3 == points[2].primitive)

    def test_rect_builder(self):
        scene = create_scene()
        builder = RectBuilder(scene)
        builder.process_click(glm.vec2(200, 200), glm.vec3(0, 0, 0), empty_mods())
        builder.process_click(glm.vec2(300, 300), glm.vec3(1, 1, 0), empty_mods())

        objects = list(scene.objects)

        self.assertTrue(len(objects) == (8 + 6 * 2 + 12 + 6))

        points = [obj for obj in objects if isinstance(obj, ScenePoint)]
        edges = [obj for obj in objects if isinstance(obj, SceneEdge)]
        faces = [obj for obj in objects if isinstance(obj, SceneFace)]

        self.assertTrue(len(points) == 8)
        self.assertTrue(len(edges) == 18)
        self.assertTrue(len(faces) == 6 * 2)


class SceneObjectTests(unittest.TestCase):
    def setUp(self):
        RawSceneObject.MESH_PROVIDER = TestMeshProvider()

    def test_same_id(self):
        point = Point(glm.vec3())
        obj = ScenePoint(point)
        self.assertTrue(point.id == obj.id)

    def test_same_name(self):
        point = Point(glm.vec3())
        obj = ScenePoint(point)
        self.assertTrue(point.name == obj.name)

    def test_line_by_two_points_hierarchy(self):
        point1 = ScenePoint.by_pos(glm.vec3(0, 0, 1))
        point2 = ScenePoint.by_pos(glm.vec3(1, 0, 1))
        line = SceneLine.by_two_points(point1, point2)

        parents = list(line.parents)
        children = list(line.children)

        self.assertTrue(len(children) == 0)

        self.assertSequenceEqual(parents, [point1, point2])

    def test_line_by_point_and_line_hierarchy(self):
        point1 = ScenePoint.by_pos(glm.vec3(0, 0, 1))
        point2 = ScenePoint.by_pos(glm.vec3(1, 0, 1))
        point3 = ScenePoint.by_pos(glm.vec3(2, 0, 1))
        line1 = SceneLine.by_two_points(point1, point2)
        line2 = SceneLine.by_point_and_line(point3, line1)

        parents = list(line2.parents)
        children = list(line2.children)

        self.assertTrue(len(children) == 0)

        self.assertSequenceEqual(parents, [point3, line1])

    def test_edge_hierarchy(self):
        point1 = ScenePoint.by_pos(glm.vec3(0, 0, 1))
        point2 = ScenePoint.by_pos(glm.vec3(1, 0, 1))
        edge = SceneEdge.by_two_points(point1, point2)

        parents = list(edge.parents)
        children = list(edge.children)

        self.assertTrue(len(children) == 0)

        self.assertSequenceEqual(parents, [point1, point2])

    def test_plane_by_three_points_hierarchy(self):
        point1 = ScenePoint.by_pos(glm.vec3(0, 0, 1))
        point2 = ScenePoint.by_pos(glm.vec3(1, 0, 1))
        point3 = ScenePoint.by_pos(glm.vec3(2, 0, 1))
        plane = ScenePlane.by_three_points(point1, point2, point3)

        parents = list(plane.parents)
        children = list(plane.children)

        self.assertTrue(len(children) == 0)

        self.assertSequenceEqual(parents, [point1, point2, point3])

    def test_plane_by_point_and_plane_hierarchy(self):
        point1 = ScenePoint.by_pos(glm.vec3(0, 0, 1))
        point2 = ScenePoint.by_pos(glm.vec3(1, 0, 1))
        point3 = ScenePoint.by_pos(glm.vec3(2, 0, 1))
        point4 = ScenePoint.by_pos(glm.vec3(2, 0, 2))
        plane1 = ScenePlane.by_three_points(point1, point2, point3)
        plane2 = ScenePlane.by_point_and_plane(point4, plane1)

        parents = list(plane2.parents)
        children = list(plane2.children)

        self.assertTrue(len(children) == 0)

        self.assertSequenceEqual(parents, [point4, plane1])

    def test_plane_by_point_and_line_hierarchy(self):
        point1 = ScenePoint.by_pos(glm.vec3(0, 0, 1))
        point2 = ScenePoint.by_pos(glm.vec3(1, 0, 1))
        point3 = ScenePoint.by_pos(glm.vec3(2, 0, 1))
        line = SceneLine.by_two_points(point1, point2)
        plane = ScenePlane.by_point_and_line(point3, line)

        parents = list(plane.parents)
        children = list(plane.children)

        self.assertTrue(len(children) == 0)

        self.assertSequenceEqual(parents, [point3, line])

    def test_plane_by_point_and_edge_hierarchy(self):
        point1 = ScenePoint.by_pos(glm.vec3(0, 0, 1))
        point2 = ScenePoint.by_pos(glm.vec3(1, 0, 1))
        point3 = ScenePoint.by_pos(glm.vec3(2, 0, 1))
        edge = SceneEdge.by_two_points(point1, point2)
        plane = ScenePlane.by_point_and_segment(point3, edge)

        parents = list(plane.parents)
        children = list(plane.children)

        self.assertTrue(len(children) == 0)

        self.assertSequenceEqual(parents, [point3, edge])

    def test_face_hierarchy(self):
        point1 = ScenePoint.by_pos(glm.vec3(0, 0, 1))
        point2 = ScenePoint.by_pos(glm.vec3(1, 0, 1))
        point3 = ScenePoint.by_pos(glm.vec3(2, 0, 1))
        face = SceneFace.by_three_points(point1, point2, point3)

        parents = list(face.parents)
        children = list(face.children)

        self.assertTrue(len(children) == 0)

        self.assertSequenceEqual(parents, [point1, point2, point3])

    def test_parent_added_to_child(self):
        point1 = ScenePoint.by_pos(glm.vec3())
        point2 = ScenePoint.by_pos(glm.vec3())
        point1.add_children(point2)

        self.assertTrue(len(list(point1.parents)) == 0)
        self.assertTrue(len(list(point2.children)) == 0)

        self.assertTrue(point1 in list(point2.parents))
        self.assertTrue(point2 in list(point1.children))

    def test_child_added_to_parent(self):
        point1 = ScenePoint.by_pos(glm.vec3())
        point2 = ScenePoint.by_pos(glm.vec3())
        point2.add_parents(point1)

        self.assertTrue(len(list(point1.parents)) == 0)
        self.assertTrue(len(list(point2.children)) == 0)

        self.assertTrue(point1 in list(point2.parents))
        self.assertTrue(point2 in list(point1.children))


class TransformTests(unittest.TestCase):
    def test_translate(self):
        transform = Transform()
        transform.translate_by(glm.vec3(1, 1, 3))

        self.assertTrue(transform.translation == glm.vec3(1, 1, 3))

    def test_identity_directions(self):
        transform = Transform()
        self.assertTrue(transform.forward == glm.vec3(0, 0, 1))
        self.assertTrue(transform.right == glm.vec3(1, 0, 0))
        self.assertTrue(transform.up == glm.vec3(0, 1, 0))

    def test_rotation(self):
        transform = Transform()
        transform.rotate_by(glm.vec3(0, 90, 0))

        self.assert_vec_almost_equal(glm.vec3(0, glm.pi() / 2, 0), transform.eulers)

    def test_rotation_directions(self):
        transform = Transform()
        transform.rotate_by(glm.vec3(0, 90, 0))

        self.assert_vec_almost_equal(glm.vec3(0, 1, 0), transform.up)
        self.assert_vec_almost_equal(glm.vec3(0, 0, -1), transform.right)
        self.assert_vec_almost_equal(glm.vec3(1, 0, 0), transform.forward)

    def assert_vec_almost_equal(self, v1, v2):
        self.assertTrue(glm.distance(v1, v2) < 1e-3)


class EventTests(unittest.TestCase):
    def test_event_local_func(self):
        event = Event()

        passed = False

        def do():
            nonlocal passed
            passed = True

        event += do
        event.invoke()

        self.assertTrue(passed)

    def test_event_args(self):
        event = Event()

        passed = False

        def do(*args):
            nonlocal passed
            passed = args[0] == 1

        event += do
        event.invoke(1, 2)

        self.assertTrue(passed)

    def test_event_unsubscribe(self):
        event = Event()

        passed = True

        def do():
            nonlocal passed
            passed = False

        event += do
        event -= do
        event.invoke()

        self.assertTrue(passed)

    def test_event_mixed_unsubscribe(self):
        event = Event()

        passed = False

        def do1():
            nonlocal passed
            passed = False

        def do2():
            nonlocal passed
            passed = True

        event += do1
        event += do2
        event -= do1
        event.invoke()

        self.assertTrue(passed)


if __name__ == "__main__":
    unittest.main()
