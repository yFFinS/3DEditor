from typing import Optional

import numpy as np
import glm
from PyQt5.QtGui import QMouseEvent


def to_float32_array(array):
    return np.array(array, dtype=np.float32)


def to_uint32_array(array):
    return np.array(array, dtype=np.uint32)


def as_uint32_array(value):
    return to_uint32_array([value])


def empty_float32_array():
    return np.array([], dtype=np.float32)


def empty_uint32_array():
    return np.array([], dtype=np.uint32)


def almost_equal(f1, f2):
    return abs(f1 - f2) < 1e-8


def almost_equal_vec(v1, v2):
    return glm.distance2(v1, v2) < 1e-8


def pyramid_volume_sign(s, t1, t2, t3):
    """ Вычисляет знак объёма треугольной пирамиды """

    return glm.sign(glm.dot(glm.cross(t1 - s, t2 - s), t3 - s))


def ray_plane_intersection_distance(origin: glm.vec3, direction: glm.vec3,
                                    point: glm.vec3, norm: glm.vec3) -> float:
    den = glm.dot(direction, norm)
    if almost_equal(den, 0):
        return np.nan

    return glm.dot(point - origin, norm) / den


def ray_plane_intersection(origin: glm.vec3, direction: glm.vec3,
                           point: glm.vec3, norm: glm.vec3) -> glm.vec3:
    distance = ray_plane_intersection_distance(origin, direction, point, norm)
    return origin + distance * direction


def point_to_line_distance(point: glm.vec2, line1: glm.vec2,
                           line2: glm.vec2) -> float:
    p = line1 - point
    dir_vec = glm.normalize(line2 - line1)
    return abs(p.x * dir_vec.y - dir_vec.x * p.y)


def point_to_point_distance(point1: glm.vec2, point2: glm.vec2) -> float:
    return glm.distance(point1, point2)


def point_to_segment_distance(point: glm.vec2, segment1: glm.vec2,
                              segment2: glm.vec2) -> float:
    S1S2 = segment2 - segment1
    S1P = point - segment1
    S2P = point - segment2

    if glm.dot(S1S2, S2P) > 0:
        return glm.length(S2P)
    if glm.dot(S1S2, S1P) < 0:
        return glm.length(S1P)

    return point_to_line_distance(point, segment1, segment2)


def extract_pos(event: QMouseEvent) -> glm.vec2:
    pos = event.pos()
    return glm.vec2(pos.x(), pos.y())


def round_vec3(vec3: glm.vec3, digits: int = 4) -> glm.vec3:
    return glm.vec3(round(vec3.x, digits), round(vec3.y, digits),
                    round(vec3.z, digits))


def is_inside_polygon(point: glm.vec2, polygon: list[glm.vec2]) -> bool:
    """https://wrf.ecse.rpi.edu/Research/Short_Notes/pnpoly.html"""
    result = False
    j = len(polygon) - 1
    for i in range(len(polygon)):
        if (((polygon[i].y > point.y) != (polygon[j].y > point.y)) and
                (point.x < (polygon[j].x - polygon[i].x) * (
                        point.y - polygon[i].y) / (
                         polygon[j].y - polygon[i].y) + polygon[i].x)):
            result = not result
        j = i
    return result


def ray_triangle_intersection_distance(origin: glm.vec3, direction: glm.vec3,
                                       point1: glm.vec3, point2: glm.vec3,
                                       point3: glm.vec3) -> float:
    """https://en.wikipedia.org/wiki/M%C3%B6ller%E2%80%93Trumbore_intersection_algorithm"""

    eps = 1e-5
    edge1 = point2 - point1
    edge2 = point3 - point1
    h = glm.cross(direction, edge2)
    a = glm.dot(edge1, h)
    if abs(a) < eps:
        return np.nan
    f = 1.0 / a
    s = origin - point1
    u = f * glm.dot(s, h)
    if u < 0 or u > 1:
        return np.nan
    q = glm.cross(s, edge1)
    v = f * glm.dot(direction, q)
    if v < 0 or u + v > 1:
        return np.nan

    t = f * glm.dot(edge2, q)
    return t if t > eps else np.nan


def ray_triangle_intersection(origin: glm.vec3, direction: glm.vec3,
                              point1: glm.vec3, point2: glm.vec3,
                              point3: glm.vec3) -> glm.vec3:
    distance = ray_triangle_intersection_distance(origin, direction, point1,
                                                  point2, point3)
    return origin + distance * direction


def closest_point_on_segment(p, s1, s2):
    distance = point_to_segment_distance(p, s1, s2)
    S1P = glm.distance(s1, p)
    if abs(distance - S1P) < 1e-5:
        return s1

    S2P = glm.distance(s2, p)
    if abs(distance - S2P) < 1e-5:
        return s2

    dir_vec = s2 - s1
    norm_vec = glm.normalize(glm.vec2(-dir_vec.y, dir_vec.x))
    v1 = p + norm_vec * distance
    d2 = v1 - s1

    if abs(d2.x * dir_vec.y - d2.y * dir_vec.x) < 1e-4:
        return v1
    return p - norm_vec * dir_vec


def line_line_intersection(a1, a2, b1, b2) -> Optional[glm.vec3]:
    da = a2 - a1
    db = b2 - b1
    dc = b1 - a1

    if abs(glm.dot(dc, glm.cross(da, db))) > 1e-4:
        return None

    s = glm.dot(glm.cross(dc, db), glm.cross(da, db)) / glm.length2(
        glm.cross(da, db))
    if 0 <= s <= 1:
        return a1 + da * s

    return None
