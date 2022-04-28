# import glm
#
#
# class BaseGeometryObject:
#     def get_dist_to_screen_pos(self, screen_pos, transform):
#         # TODO
#         """
#         :param glm.vec2 screen_pos: Координаты точки на экране
#         :param func transform: Функция, которая переводит точку glm.vec3 в соответствующую ей точку glm.vec2 нг экране
#         :return: Расстояние от screen_pos до объекта
#         """
#         raise NotImplementedError
#
#     def get_dist_to_point(self, point):
#         """Возвращает дистанцию до точки"""
#         pass
#
#     def get_dist_to_line(self, line):
#         """Возвращает дистанцию до прямой"""
#         pass
#
#     def get_dist_to_plane(self, plane):
#         """Возвращает дистанцию до плоскости"""
#         pass
#
#
# class Point(BaseGeometryObject):
#     def __init__(self, x, y, z):
#         self.position = glm.vec3(x, y, z)
#
#     @property
#     def xyz(self):
#         return self.position
#
#     @property
#     def x(self):
#         return self.position.x
#
#     @property
#     def y(self):
#         return self.position.y
#
#     @property
#     def z(self):
#         return self.position.z
#
#     def get_dist_to_point(self, point):
#         pass
#
#     def get_dist_to_line(self, line):
#         pass
#
#     def get_dist_to_plane(self, plane):
#         pass
#
#
# class BaseLine(BaseGeometryObject):
#     def get_pivot_points(self):
#         """Возвращает две различные точки, принадлежащие прямой"""
#         pass
#
#     def get_directional_vector(self):
#         """Возвращает направляющий вектор прямой"""
#         pass
#
#
# class LineBy2Points(BaseLine):
#     def __init__(self, point1, point2):
#         self.point1 = point1
#         self.point2 = point2
#
#     def get_dist_to_point(self, point):
#         pass
#
#     def get_dist_to_line(self, line):
#         pass
#
#     def get_dist_to_plane(self, plane):
#         pass
#
#     def get_pivot_points(self):
#         return self.point1.xyz, self.point2.xyz
#
#     def get_directional_vector(self):
#         return self.point2.xyz - self.point1.xyz
#
#
# class LineByPointAndLine(BaseLine):
#     def __init__(self, point, line):
#         self.point = point
#         self.line = line
#
#     def get_dist_to_point(self, point):
#         pass
#
#     def get_dist_to_line(self, line):
#         pass
#
#     def get_dist_to_plane(self, plane):
#         pass
#
#     def get_pivot_points(self):
#         return self.point.xyz, (self.point.xyz + self.line.get_direction_vector()).xyz
#
#     def get_directional_vector(self):
#         return self.line.get_direction_vector()
#
#
# def is_coplanar(point1, point2, point3):
#     mixed = glm.dot(glm.cross(point1 - point2, point2 - point3), point3 - point1)
#     return abs(mixed) < 1e-9
#
#
# class BasePlane(BaseGeometryObject):
#     def get_pivot_points(self):
#         pass
#
#     def get_direction_vectors(self):
#         pass
#
#
# class PlaneBy3Points(BasePlane):
#     def __init__(self, point1, point2, point3):
#         self.point1 = point1
#         self.point2 = point2
#         self.point3 = point3
#
#     def get_dist_to_point(self, point):
#         pass
#
#     def get_dist_to_line(self, line):
#         pass
#
#     def get_dist_to_plane(self, plane):
#         pass
#
#     def get_pivot_points(self):
#         return self.point1.xyz, self.point2.xyz, self.point3.xyz
#
#     def get_direction_vectors(self):
#         return self.point2.xyz - self.point1.xyz, self.point3.xyz - self.point2.xyz
#
#
# class PlaneByPointAndPlane(BasePlane):
#     def __init__(self, point, plane):
#         self.point = point
#         self.plane = plane
#
#     def get_dist_to_point(self, point):
#         pass
#
#     def get_dist_to_line(self, line):
#         pass
#
#     def get_dist_to_plane(self, plane):
#         pass
#
#     def get_pivot_points(self):
#         pass
#
#     def get_direction_vectors(self):
#         pass
