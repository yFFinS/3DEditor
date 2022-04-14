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

    def get_dist_to_point(self, point):
        """Возвращает дистанцию до точки"""
        pass

    def get_dist_to_line(self, line):
        """Возвращает дистанцию до прямой"""
        pass

    def get_dist_to_plane(self, plane):
        """Возвращает дистанцию до плоскости"""
        pass

    def get_serializing_dict(self):
        pass


class Point(BaseGeometryObject):
    __counter = 1

    def __init__(self, pos, name=None, id=None):
        if name is None:
            name = f'Point{Point.__counter}'
            Point.__counter += 1
        super(Point, self).__init__(name, id)
        self.__type = "point"
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
        return {self.id:
            {
                "type": self.type,
                "name": self.name,
                "forming objects": [self.x, self.y, self.z]
            }
        }

    def get_dist_to_point(self, point):
        pass

    def get_dist_to_line(self, line):
        pass

    def get_dist_to_plane(self, plane):
        pass


class BaseLine(BaseGeometryObject):
    __counter = 0

    def __init__(self, name=None, id=None):
        if name is None:
            name = f'Line{BaseLine.__counter}'
            BaseLine.__counter += 1
        super(BaseLine, self).__init__(name, id)
        self.__type = "line"

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
        return None


class LineBy2Points(BaseLine):
    def __init__(self, point1, point2, name=None, id=None):
        super(LineBy2Points, self).__init__(name, id)
        self.point1 = point1
        self.point2 = point2

    def get_serializing_dict(self):
        return {self.id:
            {
                "type": self.type,
                "name": self.name,
                "forming objects": [self.point1.id, self.point2.id]
            }
        }

    def get_dist_to_point(self, point):
        pass

    def get_dist_to_line(self, line):
        pass

    def get_dist_to_plane(self, plane):
        pass

    def get_pivot_points(self):
        return self.point1.xyz, self.point2.xyz

    def get_directional_vector(self):
        return self.point2.xyz - self.point1.xyz


class LineByPointAndLine(BaseLine):
    def __init__(self, name, point, line):
        super(LineByPointAndLine, self).__init__(name)
        self.point = point
        self.line = line

    def get_serializing_dict(self):
        return {self.id:
            {
                "type": self.type,
                "name": self.name,
                "forming objects": [self.point.id, self.line.id]
            }
        }

    def get_dist_to_point(self, point):
        pass

    def get_dist_to_line(self, line):
        pass

    def get_dist_to_plane(self, plane):
        pass

    def get_pivot_points(self):
        return self.point.xyz, self.point.xyz + self.line.get_direction_vector()

    def get_directional_vector(self):
        return self.line.get_direction_vector()


class BasePlane(BaseGeometryObject):
    __counter = 1

    def __init__(self, name=None, id=None):
        if name is None:
            name = f'Plane{BasePlane.__counter}'
            BasePlane.__counter += 1

        super(BasePlane, self).__init__("plane", name, id)

    @staticmethod
    def is_coplanar(point1, point2, point3):
        """Возвращает True, если точки компланарны и False в противном случае"""
        mixed = glm.dot(glm.cross(point1 - point2, point2 - point3),
                        point3 - point1)
        return abs(mixed) < 1e-9

    def get_pivot_points(self):
        """Возвращает три различные точки на плоскости"""
        pass

    def get_direction_vectors(self):
        """Возвращает направляющие векторы плоскости"""
        pass


class PlaneBy3Points(BasePlane):
    def __init__(self, point1, point2, point3, name=None, id=None):
        super(PlaneBy3Points, self).__init__(name, id)
        self.point1 = point1
        self.point2 = point2
        self.point3 = point3

    def get_serializing_dict(self):
        return {self.id:
            {
                "type": self.type,
                "name": self.name,
                "forming objects": [self.point1.id, self.point2.id,
                                    self.point3.id]
            }
        }

    def get_dist_to_point(self, point):
        pass

    def get_dist_to_line(self, line):
        pass

    def get_dist_to_plane(self, plane):
        pass

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
        return {self.id:
            {
                "type": self.type,
                "name": self.name,
                "forming objects": [self.point.id, self.plane.id]
            }
        }

    def get_dist_to_point(self, point):
        pass

    def get_dist_to_line(self, line):
        pass

    def get_dist_to_plane(self, plane):
        pass

    def get_pivot_points(self):
        dir_vectors = self.get_direction_vectors()
        return self.point.pos, self.point.pos + dir_vectors[0], \
               self.point.pos + dir_vectors[1]

    def get_direction_vectors(self):
        return self.plane.get_directional_vectors()


class Segment(BaseGeometryObject):
    def __init__(self, point1, point2, name=None, id=None):
        super(Segment, self).__init__('segment', name, id)
        self.point1 = point1
        self.point2 = point2

    def get_serializing_dict(self):
        return {self.id:
            {
                "type": self.type,
                "name": self.name,
                "forming objects": [self.point1.id, self.point2.id]
            }
        }

    def get_dist_to_point(self, point):
        pass

    def get_dist_to_line(self, line):
        pass

    def get_dist_to_plane(self, plane):
        pass

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


class BaseVolumetricBody(BaseGeometryObject):
    def __init__(self, points, name=None, id=None):
        super(BaseVolumetricBody, self).__init__('base_3d_body', name, id)
        self.points = points

    def get_dist_to_plane(self, plane):
        raise Exception("Not implement")

    def get_dist_to_line(self, line):
        raise Exception("Not implement")

    def get_dist_to_point(self, point):
        raise Exception("Not implement")

    def get_serializing_dict(self):
        return {self.id:
            {
                "name": self.name,
                "type": self.type,
                "forming objects": self.points
            }
        }


if __name__ == '__main__':
    print('Py equal shit')
