import glm
import numpy as np
from .transform import Transform


class Camera(Transform):
    def __init__(self, width: int, height: int):
        super(Camera, self).__init__()

        self.__fov = 100
        self.__min_z = 0.01
        self.__max_z = 1000
        self.__width = width
        self.__height = height

        self.__view_mat = glm.mat4(1)
        self.__proj_mat = glm.mat4(1)
        self.__pv_mat = glm.mat4(1)

        self.translation = glm.vec3(-5, 2, -5)

        self.__recalculate_proj_matrix()

    def _transform_changed(self):
        super(Camera, self)._transform_changed()
        self.__recalculate_view_matrix()

    @property
    def fov(self) -> float:
        return self.__fov

    @fov.setter
    def fov(self, value: float):
        if value <= 0.01:
            return
        self.__fov = value
        self.__recalculate_proj_matrix()

    @property
    def min_z(self) -> float:
        return self.__min_z

    @min_z.setter
    def min_z(self, value: float):
        if value <= 0.01:
            return
        self.__min_z = value
        self.__recalculate_proj_matrix()

    @property
    def max_z(self) -> float:
        return self.__max_z

    @max_z.setter
    def max_z(self, value: float):
        if value <= 0.01:
            return
        self.__max_z = value
        self.__recalculate_proj_matrix()

    @property
    def width(self) -> float:
        return self.__width

    @width.setter
    def width(self, value: float):
        if value <= 1:
            return
        self.__width = value

    @property
    def height(self) -> float:
        return self.__height

    @height.setter
    def height(self, value: float):
        if value <= 1:
            return
        self.__height = value

    @property
    def proj_view_matrix(self) -> glm.mat4:
        return self.__pv_mat

    @property
    def view_matrix(self) -> glm.mat4:
        return glm.lookAt(self.translation, self.translation + self.forward, self.up)

    @property
    def proj_matrix(self) -> glm.mat4:
        return glm.perspective(glm.radians(self.fov), self.width / self.height, self.min_z, self.max_z)

    def get_mvp(self, model_mat: glm.mat4) -> glm.mat4:
        return self.proj_view_matrix * model_mat

    def world_to_screen(self, world_pos: glm.vec3) -> glm.vec2:
        device_space = glm.vec2(self.world_to_device(world_pos))
        if glm.isinf(device_space.x):
            return glm.vec2(np.inf)
        return ((device_space + 1) / 2) * glm.vec2(self.width, self.height)

    def screen_to_world(self, screen_pos: glm.vec2) -> glm.vec3:
        screen = glm.vec4(2.0 * screen_pos.x / self.width - 1, -(2.0 * screen_pos.y / self.height - 1), -1, 1)
        view = glm.inverse(self.proj_matrix) * screen
        view = glm.vec4(view.x, view.y, -1, 0)
        ray = glm.inverse(self.view_matrix) * view
        return glm.normalize(glm.vec3(ray))

    def world_to_device(self, world_pos: glm.vec3) -> glm.vec3:
        clip_space = self.proj_matrix * (self.view_matrix * glm.vec4(world_pos, 1))
        if abs(clip_space.w) < 1e-8:
            return glm.vec3(np.inf)
        return glm.vec3(clip_space.x, clip_space.y, clip_space.z) / clip_space.w

    def get_frustum_edges(self) -> list[glm.vec3]:
        fov = glm.radians(self.fov)
        aspect = self.width / self.height
        h_near = 2 * np.tan(fov / 2) * self.min_z
        w_near = h_near * aspect
        h_far = 2 * np.tan(fov / 2) * self.max_z
        w_far = h_far * aspect

        look_dir = self.forward
        up = self.up
        right = self.right

        center_near = self.translation + look_dir * self.min_z
        center_far = self.translation + look_dir * self.max_z

        top_left_near = center_near + (up * (h_near / 2)) - (right * (w_near / 2))
        top_right_near = center_near + (up * (h_near / 2)) + (right * (w_near / 2))
        bot_left_near = center_near - (up * (h_near / 2)) - (right * (w_near / 2))
        bot_right_near = center_near - (up * (h_near / 2)) + (right * (w_near / 2))

        top_left_far = center_far + (up * (h_far / 2)) - (right * (w_far / 2))
        top_right_far = center_far + (up * (h_far / 2)) + (right * (w_far / 2))
        bot_left_far = center_far - (up * (h_far / 2)) - (right * (w_far / 2))
        bot_right_far = center_far - (up * (h_far / 2)) + (right * (w_far / 2))
        return [top_left_near, top_right_near, bot_left_near, bot_right_near,
                top_left_far, top_right_far, bot_left_far, bot_right_far]

    def __recalculate_view_matrix(self):
        self.__view_mat = glm.lookAt(self.translation, self.translation + self.forward, self.up)
        self.__recalculate_pv_matrix()

    def __recalculate_proj_matrix(self):
        self.__proj_mat = glm.perspective(glm.radians(self.fov), self.width / self.height, self.min_z, self.max_z)
        self.__recalculate_pv_matrix()

    def __recalculate_pv_matrix(self):
        self.__pv_mat = self.proj_matrix * self.view_matrix


