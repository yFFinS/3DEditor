import glm
import numpy as np
from scene import BaseTransform
from PyQt5.QtCore import Qt


class Camera(BaseTransform):
    default_position = glm.vec3(-5, 2, -5)
    default_rotation = glm.quat(glm.vec3(0.3, 0.4, 0.3))

    def __init__(self, width, height):
        super(Camera, self).__init__()
        self.translation = self.default_position
        self.rotation = glm.quat()
        self.fov = 60
        self.min_z = 0.01
        self.max_z = 100
        self.width = width
        self.height = height

    def get_view_mat(self):
        return glm.lookAt(self.translation, self.translation + self.get_forward(), self.get_up())

    def get_proj_mat(self):
        return glm.perspective(glm.radians(self.fov), self.width / self.height, self.min_z, self.max_z)

    def get_mvp(self, model_mat):
        return self.get_proj_mat() * self.get_view_mat() * model_mat

    def world_to_screen_space(self, vec3):
        device_space = self.to_device_space_2d(vec3)
        if not device_space:
            return None
        return ((device_space + 1) / 2) * glm.vec2(self.width, self.height)

    def screen_to_world(self, pos):
        screen = glm.vec4(2.0 * pos.x / self.width - 1, -(2.0 * pos.y / self.height - 1), -1, 1)
        view = glm.inverse(self.get_proj_mat()) * screen
        view = glm.vec4(view.x, view.y, -1, 0)
        ray = glm.inverse(self.get_view_mat()) * view
        return glm.normalize(glm.vec3(ray))

    def to_device_space_2d(self, vec3):
        clip_space = self.get_proj_mat() * (self.get_view_mat() * glm.vec4(vec3, 1))
        if abs(clip_space.w) < 1e-8:
            return None
        device_space = glm.vec3(clip_space.x, clip_space.y, clip_space.z) / clip_space.w
        return glm.vec2(device_space)

    def get_frustum_edges(self):
        fov = glm.radians(self.fov)
        aspect = self.width / self.height
        h_near = 2 * np.tan(fov / 2) * self.min_z
        w_near = h_near * aspect
        h_far = 2 * np.tan(fov / 2) * self.max_z
        w_far = h_far * aspect

        look_dir = self.get_forward()
        up = self.get_up()
        right = self.get_right()

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


class CameraController:
    def __init__(self, camera):
        self.camera = camera
        self.move_speed = 0.1
        self.mouse_sensitivity = 0.003
        self.min_rotate_delta = 1

        self.__last_mouse_pos = glm.vec2()
        self.__mouse_rotating = False
        self.__rotation_eulers = glm.eulerAngles(camera.rotation)

    def handle_scroll(self, gl_widget, event):
        scroll = event.angleDelta().y()
        self.camera.move_by(0, 0, glm.sign(scroll) * self.move_speed)

        gl_widget.update()

    def handle_mouse_move(self, gl_widget, event):
        if not self.__mouse_rotating:
            return
        pos = event.pos()
        pos = glm.vec2(pos.x(), pos.y())
        delta = pos - self.__last_mouse_pos

        if abs(delta.x) < self.min_rotate_delta:
            delta.x = 0
        if abs(delta.y) < self.min_rotate_delta:
            delta.y = 0

        delta *= self.mouse_sensitivity
        self.__last_mouse_pos = pos
        self.__rotation_eulers += glm.vec3(-delta.y, delta.x, 0)
        self.camera.rotation = glm.quat(self.__rotation_eulers)
        gl_widget.update()

    def handle_mouse_press(self, gl_widget, event):
        button = event.button()
        if button != Qt.MiddleButton:
            return
        pos = event.pos()
        pos = glm.vec2(pos.x(), pos.y())
        self.__last_mouse_pos = pos
        self.__mouse_rotating = True

    def handle_mouse_release(self, gl_widget, event):
        button = event.button()
        if button != Qt.MiddleButton:
            return
        self.__last_mouse_pos = glm.vec2()
        self.__mouse_rotating = False
