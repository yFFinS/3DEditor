import glm


class BaseGeometryObject:
    def get_dist_to_point(self, point):
        """Возвращает дистанцию до точки"""
        pass

    def get_dist_to_line(self, line):
        """Возвращает дистанцию до прямой"""
        pass

    def get_dist_to_plane(self, plane):
        """Возвращает дистанцию до плоскости"""
        pass


class Point(BaseGeometryObject):
    def __init__(self, x, y, z):
        self.position = glm.vec3(x, y, z)

    @property
    def x(self):
        return self.position.x

    @property
    def y(self):
        return self.position.y

    @property
    def z(self):
        return self.position.z

    def get_dist_to_point(self, point):
        pass

    def get_dist_to_line(self, line):
        pass

    def get_dist_to_plane(self, plane):
        pass


class BaseLine(BaseGeometryObject):
    def get_pivot_points(self):
        """Возвращает две различные точки, принадлежащие прямой"""
        pass

    def get_directional_vector(self):
        """Возвращает направляющий вектор прямой"""
        pass


class LineBy2Points(BaseLine):
    def __init__(self, point1, point2):
        self.point1 = point1
        self.point2 = point2

    def get_dist_to_point(self, point):
        pass

    def get_dist_to_line(self, line):
        pass

    def get_dist_to_plane(self, plane):
        pass

    def get_pivot_points(self):
        return self.point1, self.point2

    def get_directional_vector(self):
        return self.point2 - self.point1


class LineByPointAndLine(BaseLine):
    def __init__(self, point, line):
        self.point = point
        self.line = line

    def get_dist_to_point(self, point):
        pass

    def get_dist_to_line(self, line):
        pass

    def get_dist_to_plane(self, plane):
        pass

    def get_pivot_points(self):
        return self.point, (self.point + self.line.get_direction_vector()).xyz

    def get_directional_vector(self):
        return self.line.get_direction_vector()


def is_coplanar(point1, point2, point3):
    mixed = glm.dot(glm.cross(point1 - point2, point2 - point3), point3 - point1)
    return abs(mixed) < 1e-9


class BasePlane(BaseGeometryObject):
    def get_pivot_points(self):
        pass

    def get_direction_vectors(self):
        pass


class PlaneBy3Points(BasePlane):
    def __init__(self, point1, point2, point3):
        if is_coplanar(point1, point2, point3):
            raise Exception("Ожидались некомпланарные точки")
        self.__point1 = point1
        self.__point2 = point2
        self.__point3 = point3

    @property
    def point1(self):
        return self.__point1.xyz

    @property
    def point2(self):
        return self.__point2.xyz

    @property
    def point3(self):
        return self.__point3.xyz

    def get_dist_to_point(self, point):
        pass

    def get_dist_to_line(self, line):
        pass

    def get_dist_to_plane(self, plane):
        pass

    def get_pivot_points(self):
        return self.__point1, self.__point2, self.__point3

    def get_direction_vectors(self):
        return self.__point2 - self.__point1, self.__point3 - self.__point2


class PlaneByPointAndPlane(BasePlane):
    def __init__(self, point, plane):
        self.__point = point
        self.__plane = plane

    @property
    def point(self):
        return self.__point

    @property
    def plane(self):
        return self.__plane

    def get_dist_to_point(self, point):
        pass

    def get_dist_to_line(self, line):
        pass

    def get_dist_to_plane(self, plane):
        pass

    def get_pivot_points(self):
        pass

    def get_direction_vectors(self):
        pass
