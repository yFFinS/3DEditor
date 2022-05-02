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


def intersect_line_plane(l1, l2, point, norm):
    dir_v = glm.normalize(l2 - l1)
    den = glm.dot(dir_v, norm)
    if almost_equal(den, 0):
        return None

    dist = glm.dot(point - l1, norm) / den
    return l1 + dir_v * dist


def intersect_line_triangle(l1, l2, t1, t2, t3):
    """ Находит точку пересечения прямой и треугольника """
    plane_intersection = intersect_line_plane(l1, l2, t1, glm.cross(t2 - t1, t3 - t1))
    if not plane_intersection:
        return None
    t1 -= plane_intersection
    t2 -= plane_intersection
    t3 -= plane_intersection
    u = glm.cross(t2, t3)
    v = glm.cross(t3, t1)
    w = glm.cross(t1, t2)
    if glm.dot(u, v) < 0 or glm.dot(u, w) < 0:
        return None
    return plane_intersection


def intersect_line_frustum(l1, l2, frustum_edges):
    """ Находит точки пересечения прямой и прямоугольников фрустума """

    tln, trn, bln, brn, tlf, trf, blf, brf = frustum_edges
    intersections = []

    def intersect(t1, t2, t3):
        intersection = intersect_line_triangle(l1, l2, t1, t2, t3)
        if intersection and not any(almost_equal_vec(intersection, prev_int) for prev_int in intersections):
            intersections.append(intersection)

    intersect(tln, trn, bln)
    intersect(bln, trn, brn)
    intersect(tlf, trf, blf)
    intersect(blf, trf, brf)

    intersect(tln, tlf, bln)
    intersect(bln, tlf, blf)
    intersect(trn, trf, brn)
    intersect(brn, trf, brf)

    intersect(tln, tlf, trf)
    intersect(tln, trf, trn)
    intersect(bln, blf, brf)
    intersect(bln, brf, brn)

    return intersections


def extract_pos(event: QMouseEvent) -> glm.vec2:
    pos = event.pos()
    return glm.vec2(pos.x(), pos.y())


def round_vec3(vec3: glm.vec3, digits: int = 4) -> glm.vec3:
    return glm.vec3(round(vec3.x, digits), round(vec3.y, digits), round(vec3.z, digits))
