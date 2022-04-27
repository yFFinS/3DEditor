import glm
from PyQt5.QtCore import Qt

from core.interfaces import *
from scene.camera import Camera


class CameraController(EventHandlerInterface):
    IDLE = 0
    ROTATING = 1
    MOVING = 2

    def __init__(self, camera: Camera):
        self.camera = camera
        self.scroll_speed = 0.3
        self.move_speed = 0.01
        self.rotate_speed = 0.002

        self.__rotation = camera.eulers

        self.__last_mouse_pos = glm.vec2()
        self.__state = CameraController.IDLE

    def on_wheel_scroll(self, event: QWheelEvent):
        scroll = event.angleDelta().y()
        self.camera.move_by(glm.vec3(0, 0, glm.sign(scroll) * self.scroll_speed))
        return True

    def on_mouse_move(self, event: QMouseEvent):
        if self.__state == CameraController.IDLE:
            return False

        pos = event.pos()
        pos = glm.vec2(pos.x(), pos.y())
        delta = pos - self.__last_mouse_pos
        self.__last_mouse_pos = pos

        if self.__state == CameraController.ROTATING:
            self.__rotate(delta)
        elif self.__state == CameraController.MOVING:
            self.__move(delta)

        return True

    def on_mouse_pressed(self, event: QMouseEvent):
        button = event.button()
        pos = event.pos()
        pos = glm.vec2(pos.x(), pos.y())

        if button == Qt.RightButton:
            self.__start_rotating(pos)
        elif button == Qt.MiddleButton:
            self.__start_moving(pos)

        return False

    def on_mouse_released(self, event: QMouseEvent):
        self.__state = CameraController.IDLE

    def __start_rotating(self, pivot):
        self.__last_mouse_pos = pivot
        self.__state = CameraController.ROTATING

    def __start_moving(self, pivot):
        self.__last_mouse_pos = pivot
        self.__state = CameraController.MOVING

    def __rotate(self, delta):
        delta *= self.rotate_speed
        self.__rotation += glm.vec3(delta.y, -delta.x, 0)
        self.camera.eulers = self.__rotation

    def __move(self, delta):
        move = glm.vec3(delta.x, delta.y, 0) * self.move_speed
        self.camera.move_by(move)
