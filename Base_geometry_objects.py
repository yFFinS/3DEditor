import glm
import uuid
import numpy as np

class BaseGeometryObject:
    def __init__(self, object_type, name=None, id=None):
        if id is None:
            self.__id = str(uuid.uuid4())
        else:
            self.__id = id
        self.__type = object_type
        self.name = name

    def get_dist_to_screen_pos(self, screen_pos, transform):
        # TODO
        """
        :param glm.vec2 screen_pos: Координаты точки на экране
        :param func transform: Функция, которая переводит точку glm.vec3 в соответствующую ей точку glm.vec2 нг экране
        :return: Расстояние от screen_pos до объекта
        """
        raise NotImplementedError

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

    def __add__(self, other):
        summary = self.xyz + other.xyz
        return Point(summary.x, summary.y, summary.z)

    def __sub__(self, other):
        differ = self.xyz - other.xyz
        return Point(differ.x, differ.y, differ.z)


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

    def get_dist_to_screen_pos(self, screen_pos, transform):
        transformed_point = transform(self.pos)
        return glm.distance(screen_pos, transformed_point)


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
        a1 = self.get_pivot_points()[0].xyz
        a2 = line.get_pivot_points()[0].xyz
        if abs((dir_vec1.x * dir_vec2.y - dir_vec2.x)) > 1e-9:
            coef = (a2.x - a1.x + a1.y * dir_vec1.x - a2.x * dir_vec1.x) / (dir_vec1.x * dir_vec2.y - dir_vec2.x)
            return a2 + coef * dir_vec2
        elif abs((dir_vec1.x * dir_vec2.z - dir_vec2.x)) > 1e-9:
            coef = (a2.x - a1.x + a1.z * dir_vec1.x - a2.x * dir_vec1.x) / (dir_vec1.x * dir_vec2.z - dir_vec2.x)
            return a2 + coef * dir_vec2
        else:
            coef = (a2.y - a1.y + a1.z * dir_vec1.y - a2.y * dir_vec1.y) / (dir_vec1.y * dir_vec2.z - dir_vec2.y)
            return a2 + coef * dir_vec2

        def get_dist_to_screen_pos(self, screen_pos, transform):
            p0, p1 = self.get_pivot_points()
            transformed_p0 = transform(p0.pos)
            transformed_p1 = transform(p1.pos)
            if p0 == p1:
                return glm.distance(p0, screen_pos)
            # TODO : Тут надо найти нормальное уравнение прямой
            pass


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
    def is_collinear(point1, point2, point3):
        """Возвращает True, если точки коллинеарны и False в противном случае"""
        vec1 = point2.pos - point1.pos
        vec2 = point3.pos - point2.pos
        return abs(len(glm.cross(vec1, vec2))) < 1e-9

    def get_pivot_points(self):
        """Возвращает три различные точки на плоскости"""
        pass

    def get_direction_vectors(self):
        """Возвращает направляющие векторы плоскости"""
        pass


    #TODO : Прикрутить сюда NumPy
    def get_normal_equation_form(self):
        dir_vec1, dir_vec2 = self.get_direction_vectors()
        p1, p2, p3 = self.get_pivot_points()
        x1 = p1.x; y1 = p1.y; z1 = p1.z
        x2 = p2.x; y2 = p2.y; z2 = p2.z
        x3 = p3.x; y3 = p3.y; z3 = p3.z
        #Пока не разоброался когда в знаменателе 0
        p = x3 - x1 + y3 * ((x3 - x1) / (y1 - y2)) - y1 * ((x2 - x1) / (y1 - y2))
        q = y3 * ((z2 - z1) / (y1 - y2)) + z3 - z1 - y1 * ((z2 - z1) / (y1 - y2))
        c = p / -q
        b = ((x2 - x1) + c * (z2 - z1)) / (y1 - y2)
        d = -(x1 + b * y1 + c * z1)
        a = 1
        return a, b, c, d

    def get_normal_vector(self):
        a, b, c, d = self.get_normal_equation_form()
        return glm.vec3(a, b, c)

    def get_intersection_with_plane(self, other):
        normal1 = self.get_normal_vector()
        normal2 = other.get_normal_vector()
        if abs(len(glm.cross(normal1, normal2))) < 1e-9:
            return None

    def get_dist_to_screen_pos(self, screen_pos, transform):
        a, b, c = self.get_pivot_points()
        a1 = transform(a)
        b1 = transform(b)
        c1 = transform(c)
        if not(BasePlane.is_collinear(a1, b1, c1)):
            return 0
        # TODO: Все то же нормальное уравнение прямой в плоскости
        return None

class PlaneBy3Points(BasePlane):
    def __init__(self, point1, point2, point3, name=None, id=
    None):
        if BasePlane.is_collinear(point1, point2, point3):
            raise Exception("Collinear points")
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
