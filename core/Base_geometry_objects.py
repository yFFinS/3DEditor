from _weakref import ref
from typing import Iterable

import glm
import uuid


class BaseGeometryObject:
    def __init__(self, object_type, name=None, id=None):
        if id is None:
            self.__id = str(uuid.uuid4())
        else:
            self.__id = id
        self.__type = object_type
        self.name = name

    @property
    def id(self):
        return self.__id

    @property
    def type(self):
        return self.__type

    def get_serializing_dict(self):
        pass


class Point(BaseGeometryObject):
    __counter = 1

    def __init__(self, pos, name=None, id=None):
        if name is None:
            name = f'Point{Point.__counter}'
            Point.__counter += 1

        super(Point, self).__init__("point", name, id)
        self.pos = pos

    @property
    def x(self):
        return self.pos.x

    @property
    def y(self):
        return self.pos.y

    @property
    def z(self):
        return self.pos.z

    def get_serializing_dict(self):
        return {
            self.id:
                {
                    "type": self.type,
                    "name": self.name,
                    "forming objects": [self.x, self.y, self.z]
                }
        }


class BaseLine(BaseGeometryObject):
    __counter = 0

    def __init__(self, name=None, id=None):
        if name is None:
            name = f'Line{BaseLine.__counter}'
            BaseLine.__counter += 1
        self.__type = "line"
        super(BaseLine, self).__init__(self.__type, name, id)

    def get_pivot_points(self):
        """Возвращает две различные точки, принадлежащие прямой"""
        pass

    def get_directional_vector(self):
        """Возвращает направляющий вектор прямой"""
        pass

    def get_intersection_with_line(self, line):
        dir_vec1 = self.get_directional_vector()
        dir_vec2 = line.get_directional_vector()
        if len(glm.cross(dir_vec1, dir_vec2)) == 0:
            return None
        # TODO: отлетаешь
        a1 = self.get_pivot_points()[0].xyz
        a2 = line.get_pivot_points()[0].xyz
        if abs((dir_vec1.x * dir_vec2.y - dir_vec2.x)) > 1e-9:
            coef = (a2.x - a1.x + a1.y * dir_vec1.x - a2.x * dir_vec1.x) / (
                        dir_vec1.x * dir_vec2.y - dir_vec2.x)
            return a2 + coef * dir_vec2
        elif abs((dir_vec1.x * dir_vec2.z - dir_vec2.x)) > 1e-9:
            coef = (a2.x - a1.x + a1.z * dir_vec1.x - a2.x * dir_vec1.x) / (
                        dir_vec1.x * dir_vec2.z - dir_vec2.x)
            return a2 + coef * dir_vec2
        else:
            coef = (a2.y - a1.y + a1.z * dir_vec1.y - a2.y * dir_vec1.y) / (
                        dir_vec1.y * dir_vec2.z - dir_vec2.y)
            return a2 + coef * dir_vec2


class LineBy2Points(BaseLine):
    def __init__(self, point1, point2, name=None, id=None):
        super(LineBy2Points, self).__init__(name, id)
        self.point1 = point1
        self.point2 = point2

    def get_serializing_dict(self):
        return {
            self.id:
                {
                    "type": self.type,
                    "name": self.name,
                    "forming objects": [self.point1.id, self.point2.id]
                }
        }

    def get_pivot_points(self):
        return self.point1.pos, self.point2.pos

    def get_directional_vector(self):
        return self.point2.pos - self.point1.pos


class LineByPointAndLine(BaseLine):
    def __init__(self, point, line, name=None, id=None):
        super(LineByPointAndLine, self).__init__(name, id)
        self.point = point
        self.line = line

    def get_serializing_dict(self):
        return {
            self.id:
                {
                    "type": self.type,
                    "name": self.name,
                    "forming objects": [self.point.id, self.line.id]
                }
        }

    def get_pivot_points(self):
        return self.point.pos, self.point.pos + self.line.get_directional_vector()

    def get_directional_vector(self):
        return self.line.get_directional_vector()


class BasePlane(BaseGeometryObject):
    __counter = 1

    def __init__(self, name=None, id=None):
        if name is None:
            name = f'Plane{BasePlane.__counter}'
            BasePlane.__counter += 1

        super(BasePlane, self).__init__("plane", name, id)
        self.__cuts = []

    @staticmethod
    def is_coplanar(point1, point2, point3):
        """Возвращает True, если точки компланарны и False в противном случае"""
        mixed = glm.dot(glm.cross(point1 - point2, point2 - point3),
                        point3 - point1)
        return abs(mixed) < 1e-9

    def is_collinear_to(self, plane: 'BasePlane') -> bool:
        pivots1 = self.get_pivot_points()
        pivots2 = plane.get_pivot_points()
        norm1 = glm.normalize(
            glm.cross(pivots1[0] - pivots1[1], pivots1[0] - pivots1[2]))
        norm2 = glm.normalize(
            glm.cross(pivots2[0] - pivots2[1], pivots2[0] - pivots2[2]))
        dot = glm.dot(norm1, norm2)
        return abs(abs(dot) - 1) < 1e-9

    def get_pivot_points(self):
        """Возвращает три различные точки на плоскости"""
        raise NotImplementedError

    def get_direction_vectors(self) -> (glm.vec3, glm.vec3):
        """Возвращает направляющие векторы плоскости"""
        raise NotImplementedError

    def get_normal(self) -> glm.vec3:
        dir1, dir2 = self.get_direction_vectors()
        return glm.normalize(glm.cross(dir1, dir2))

    def add_cut(self, cut_line: BaseLine):
        self.__cuts.append(ref(cut_line))

    def remove_cut(self, cut_line: BaseLine):
        self.__cuts.remove(ref(cut_line))

    @property
    def cuts(self) -> Iterable[BaseLine]:
        for cut in self.__cuts:
            yield cut()


class PlaneBy3Points(BasePlane):
    def __init__(self, point1, point2, point3, name=None, id=None):
        super(PlaneBy3Points, self).__init__(name, id)
        self.point1 = point1
        self.point2 = point2
        self.point3 = point3

    def get_serializing_dict(self):
        return {
            self.id:
                {
                    "type": self.type,
                    "name": self.name,
                    "forming objects": [self.point1.id, self.point2.id,
                                        self.point3.id],
                    "cuts": list(self.cuts)
                }
        }

    def get_pivot_points(self):
        return self.point1.pos, self.point2.pos, self.point3.pos

    def get_direction_vectors(self):
        return self.point2.pos - self.point1.pos, \
               self.point3.pos - self.point2.pos


class PlaneByPointAndPlane(BasePlane):
    def __init__(self, point, plane, name=None, id=None):
        super(PlaneByPointAndPlane, self).__init__(name, id)
        self.point = point
        self.plane = plane

    def get_serializing_dict(self):
        return {
            self.id:
                {
                    "type": self.type,
                    "name": self.name,
                    "forming objects": [self.point.id, self.plane.id],
                    "cuts": list(self.cuts)
                }
        }

    def get_pivot_points(self):
        dir_vectors = self.get_direction_vectors()
        return self.point.pos, self.point.pos + dir_vectors[0], \
               self.point.pos + dir_vectors[1]

    def get_direction_vectors(self):
        return self.plane.get_direction_vectors()


class PlaneByPointAndLine(BasePlane):
    def __init__(self, point, line, name=None, id=None):
        super(PlaneByPointAndLine, self).__init__(name, id)
        self.point = point
        self.line = line

    def get_serializing_dict(self):
        return {
            self.id:
                {
                    "type": self.type,
                    "name": self.name,
                    "forming objects": [self.point.id, self.line.id],
                    "cuts": list(self.cuts)
                }
        }

    def get_pivot_points(self):
        return self.point.pos, *self.line.get_pivot_points()

    def get_direction_vectors(self):
        pivots = self.get_pivot_points()
        return pivots[1] - pivots[0], pivots[2] - pivots[0]


class PlaneByPointAndSegment(BasePlane):
    def __init__(self, point, segment, name=None, id=None):
        super(PlaneByPointAndSegment, self).__init__(name, id)
        self.point = point
        self.segment = segment

    def get_serializing_dict(self):
        return {
            self.id:
                {
                    "type": self.type,
                    "name": self.name,
                    "forming objects": [self.point.id, self.segment.id],
                    "cuts": list(self.cuts)
                }
        }

    def get_pivot_points(self):
        return self.point.pos, self.segment.point1.pos, self.segment.point2.pos

    def get_direction_vectors(self):
        pivots = self.get_pivot_points()
        return pivots[1] - pivots[0], pivots[2] - pivots[0]


class Segment(BaseGeometryObject):
    __counter = 1

    def __init__(self, point1: Point, point2: Point, name=None, id=None):
        if name is None:
            name = f"Edge{Segment.__counter}"
            Segment.__counter += 1

        super(Segment, self).__init__('segment', name, id)
        self.point1 = point1
        self.point2 = point2

    def get_serializing_dict(self):
        return {
            self.id:
                {
                    "type": self.type,
                    "name": self.name,
                    "forming objects": [self.point1.id, self.point2.id]
                }
        }

    def get_vec(self):
        return self.point2.pos - self.point1.pos

    def get_line(self):
        return LineBy2Points(self.point1, self.point2)

    def get_intersection_with_line(self, line):
        segment_line = self.get_line()
        intersection = segment_line.get_intersection_with_line(line)
        vec_with_intersection = intersection - self.point1
        if glm.dot(vec_with_intersection, self.get_vec()) < -1e-9 or len(
                vec_with_intersection) > len(self.get_vec()) + 1e-9:
            return None
        return intersection

    def get_intersection_with_segment(self, segment):
        intersect1 = segment.get_intersection_with_line(self.get_line())
        intersect2 = self.get_intersection_with_line(segment.get_line())
        return intersect1

    def get_points(self) -> (glm.vec3, glm.vec3):
        return self.point1.pos, self.point2.pos


class Triangle(BaseGeometryObject):
    __counter = 1

    def __init__(self, point1, point2, point3, name=None, id=None):
        if name is None:
            name = f"Triangle{Triangle.__counter}"
            Triangle.__counter += 1

        super(Triangle, self).__init__('triangle', name, id)
        self.point1 = point1
        self.point2 = point2
        self.point3 = point3

    def get_serializing_dict(self):
        return {
            self.id:
                {
                    "type": self.type,
                    "name": self.name,
                    "forming objects": [self.point1.id, self.point2.id,
                                        self.point3.id]
                }
        }

    def get_points(self) -> (glm.vec3, glm.vec3, glm.vec3):
        return self.point1.pos, self.point2.pos, self.point3.pos


class BaseVolumetricBody(BaseGeometryObject):
    def __init__(self, points, name=None, id=None):
        super(BaseVolumetricBody, self).__init__('base_3d_body', name, id)
        self.points = points

    def get_serializing_dict(self):
        return {
            self.id:
                {
                    "name": self.name,
                    "type": self.type,
                    "forming objects": self.points
                }
        }
