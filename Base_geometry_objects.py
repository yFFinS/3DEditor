import glm


class BaseGeometryObject:

    def __init__(self, name):
        self.name = name

    def get_dist_to_point(self, point):
        """Возвращает дистанцию до точки"""
        pass

    def get_dist_to_line(self, line):
        """Возвращает дистанцию до прямой"""
        pass

    def get_dist_to_plane(self, plane):
        """Возвращает дистанцию до плоскости"""
        pass

    def serialize(self):
        pass


class Point(BaseGeometryObject):
    def __init__(self, name, x, y, z):
        super(Point, self).__init__(name)
        self.__position = glm.vec3(x, y, z)
        self.name = name

    @property
    def xyz(self):
        """Возвращает координаты точки в виде вектора"""
        return self.__position

    @property
    def x(self):
        return self.__position.x

    @property
    def y(self):
        return self.__position.y

    @property
    def z(self):
        return self.__position.z

    def serialize(self):
        return "point" + ";" + self.name + ";" + self.x + ";" + self.y + ";" + self.z

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
    def __init__(self, name, point1, point2):
        super(LineBy2Points, self).__init__(name)
        self.__point1 = point1
        self.__point2 = point2

    @property
    def point1(self):
        return self.__point1.xyz

    @property
    def point2(self):
        return self.__point2.xyz

    def serialize(self):
        return "line" + ";" + self.name + ";" + self.__point1.name + ";" + self.__point2.name

    def get_dist_to_point(self, point):
        pass

    def get_dist_to_line(self, line):
        pass

    def get_dist_to_plane(self, plane):
        pass

    def get_pivot_points(self):
        return self.point1, self.point2

    def get_directional_vector(self):
        return self.__point2 - self.__point1


class LineByPointAndLine(BaseLine):
    def __init__(self, name, point, line):
        super(LineByPointAndLine, self).__init__(name)
        self.__point = point
        self.__line = line

    @property
    def point(self):
        return self.__point.xyz

    @property
    def line(self):
        return self.__line

    def serialize(self):
        return "line" + ";" + self.name + ";" + self.__point + ";" + self.__line

    def get_dist_to_point(self, point):
        pass

    def get_dist_to_line(self, line):
        pass

    def get_dist_to_plane(self, plane):
        pass

    def get_pivot_points(self):
        return self.point, (self.__point + self.__line.get_direction_vector()).xyz

    def get_directional_vector(self):
        return self.line.get_direction_vector()


def is_coplanar(point1, point2, point3):
    """Возвращает True, если точки компланарны и False в противном случае"""
    mixed = glm.dot(glm.cross(point1 - point2, point2 - point3), point3 - point1)
    return abs(mixed) < 1e-9


class BasePlane(BaseGeometryObject):
    def get_pivot_points(self):
        """Возвращает три различные точки на плоскости"""
        pass

    def get_direction_vectors(self):
        """Возвращает направляющие векторы плоскости"""
        pass


class PlaneBy3Points(BasePlane):
    def __init__(self, name, point1, point2, point3):
        if is_coplanar(point1, point2, point3):
            raise Exception("Ожидались некомпланарные точки")
        super(PlaneBy3Points, self).__init__(name)
        self.__point1 = point1
        self.__point2 = point2
        self.__point3 = point3

    def serialize(self):
        return "plane" + ";" + self.__point1.name + ";" + self.__point2.name + ";" + self.__point3.name

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
    def __init__(self, name, point, plane):
        super(PlaneByPointAndPlane, self).__init__(name)
        self.__point = point
        self.__plane = plane

    @property
    def point(self):
        return self.__point

    @property
    def plane(self):
        return self.__plane

    def serialize(self):
        return "plane" + ";" + self.__point.name + ";" + self.__plane.name

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


if __name__ == '__main__':
    print('Py equal shit')
