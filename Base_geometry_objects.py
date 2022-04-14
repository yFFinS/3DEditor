import glm
import uuid


class BaseGeometryObject:

    def __init__(self, name, id = None):
        if id == None:
            self.__id = str(uuid.uuid4())
        else:
            self.__id = id
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
    def __init__(self, name, x, y, z, id=None):
        super(Point, self).__init__(name, id)
        self.__type = "point"
        self.x = x
        self.y = y
        self.z = z
        self.__position = glm.vec3(x, y, z)
        self.name = name

    @property
    def xyz(self):
        """Возвращает координаты точки в виде вектора"""
        return self.__position

    def get_serializing_dict(self):
        return { self.id :
            {
                "type" : self.type,
                "name" : self.name,
                "forming objects" : [self.x, self.y, self.z]
            }
        }

    def get_dist_to_point(self, point):
        pass

    def get_dist_to_line(self, line):
        pass

    def get_dist_to_plane(self, plane):
        pass


class BaseLine(BaseGeometryObject):

    def __init__(self, name):
        super(BaseLine, self).__init__(name)
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
            raise Exception("Прямые параллельны") #Кажется нам не нужны совпадающие прямые


class LineBy2Points(BaseLine):
    def __init__(self, name, point1, point2, id=None):
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
    def __init__(self, name, id=None):
        super(BasePlane, self).__init__(name, id)
        self.__type = "plane"

    @staticmethod
    def is_coplanar(point1, point2, point3):
        """Возвращает True, если точки компланарны и False в противном случае"""
        mixed = glm.dot(glm.cross(point1 - point2, point2 - point3), point3 - point1)
        return abs(mixed) < 1e-9

    def get_pivot_points(self):
        """Возвращает три различные точки на плоскости"""
        pass

    def get_direction_vectors(self):
        """Возвращает направляющие векторы плоскости"""
        pass


class PlaneBy3Points(BasePlane):
    def __init__(self, name, point1, point2, point3, id=None):
        if is_coplanar(point1.xyz, point2.xyz, point3.xyz):
            #А вот что делать в ините хз
            raise Exception("Ожидались некомпланарные точки")
        super(PlaneBy3Points, self).__init__(name, id)
        self.point1 = point1
        self.point2 = point2
        self.point3 = point3

    def get_serializing_dict(self):
        return {self.id:
            {
                "type": self.type,
                "name": self.name,
                "forming objects": [self.point1.id, self.point2.id, self.point3.id]
            }
        }

    def get_dist_to_point(self, point):
        pass

    def get_dist_to_line(self, line):
        pass

    def get_dist_to_plane(self, plane):
        pass

    def get_pivot_points(self):
        return self.point1.xyz, self.point2.xyz, self.point3.xyz

    def get_direction_vectors(self):
        return self.point2.xyz - self.point1.xyz, self.point3.xyz - self.point2.xyz


class PlaneByPointAndPlane(BasePlane):
    def __init__(self, name, point, plane, id=None):
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
        return self.point.xyz, self.point.xyz + dir_vectors[0], self.point.xyz + dir_vectors[1]

    def get_direction_vectors(self):
        return self.plane.get_directional_vectors()


class Segment(BaseGeometryObject):
    def __init__(self, point1, point2, id=None):
        super(Segment, self).__init__(name, id)
        self.__type = "segment"
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

    @property
    def get_vec(self):
        return self.point2.xyz - self.point1.xyz

    @property
    def get_line(self):
        return line(self.point1, self.point2)

    def get_intersection_with_line(self, line):
        segment_line = self.get_line()
        intersection = segment_line.get_intersection_with_line(line)
        vec_with_intersection = intersection - self.point1
        if glm.dot(vec_with_intersection, self.get_vec) < -1e-9 or len(vec_with_intersection) > len(self.get_vec) + 1e-9:
            raise Exception("Пересечение вне отрезка")
        return intersection

    def get_intersection_with_segment(self, segment):
        intersect1 = segment.get_intersection_with_line(self.get_line)
        intersect2 = self.get_intersection_with_line(segment.get_line)
        return intersect1

class BaseVolumetricBody(BaseGeometryObject):
    def __init__(self, name, points, id=None ):
        super(BaseVolumetricBody, self).__init__(name, id)
        self.points = points
        self.__type = "base_3d_body"

    def get_dist_to_plane(self, plane):
        raise Exception("Not implement")
    def get_dist_to_line(self, line):
        raise Exception("Not implement")
    def get_dist_to_point(self, point):
        raise Exception("Not implement")

    def get_serializing_dict(self):
        return {self.id :
            {
            "name" : self.name,
            "type" : self.type,
            "forming objects" : self.points
            }
        }


if __name__ == '__main__':
    print('Py equal shit')
