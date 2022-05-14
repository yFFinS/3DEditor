import unittest
from core.helpers import *


class IntersectionTests(unittest.TestCase):
    def test_ray_triangle(self):
        t1 = glm.vec3(1, 0, 0)
        t2 = glm.vec3(0, 1, 0)
        t3 = glm.vec3(-1, -1, 0)
        origin = glm.vec3(0, 0.1, -5)
        direction = glm.vec3(0, 0.1, 1)
        intersection = ray_triangle_intersection_distance(origin, direction, t1, t2, t3)
        self.assertFalse(glm.isnan(intersection))


if __name__ == "__main__":
    unittest.main()
