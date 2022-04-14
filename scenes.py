import glm

from buffers import *
from helpers import empty_float32_array, empty_uint32_array

from PyQt5.QtCore import Qt


class BaseTransform:
    def __init__(self):
        self.translation = glm.vec3()
        self.rotation = glm.quat()
        self.scale = glm.vec3(1)

    def rotate_by(self, x, y, z):
        self.rotation *= glm.quat(glm.vec3(x, y, z))

    def translate_by(self, x, y, z):
        self.translation += glm.vec3(x, y, z)

    def move_by(self, x, y, z):
        self.translation += x * self.get_right() + y * self.get_up() + z * self.get_forward()

    def get_forward(self):
        return self.rotation * glm.vec3(0, 0, 1)

    def get_right(self):
        return self.rotation * glm.vec3(1, 0, 0)

    def get_up(self):
        return self.rotation * glm.vec3(0, 1, 0)


class Mesh:
    def __init__(self):
        self.__vba = VertexArray()

        self.__vbo_positions = VertexBuffer()
        self.__vbo_colors = VertexBuffer()
        self.__ibo = IndexBuffer()

        self.__vba.bind_vertex_buffer(self.__vbo_positions, 0, 0, 3, GL.GL_FLOAT, 12)
        self.__vba.bind_vertex_buffer(self.__vbo_colors, 1, 1, 4, GL.GL_FLOAT, 16)
        self.__vba.bind_index_buffer(self.__ibo)

        self.__indices = empty_uint32_array()
        self.__positions = empty_float32_array()
        self.__colors = empty_float32_array()

    def set_positions(self, positions):
        self.__vbo_positions.set_data(glm.sizeof(glm.vec3) * len(positions), positions)
        self.__positions = positions.copy()

    def set_colors(self, colors):
        self.__vbo_colors.set_data(glm.sizeof(glm.vec4) * len(colors), colors)
        self.__colors = colors.copy()

    def set_indices(self, indices):
        self.__ibo.set_indices(indices)
        self.__indices = indices.copy()

    def get_positions(self):
        return self.__positions.copy()

    def get_colors(self):
        return self.__colors.copy()

    def get_indices(self):
        return self.__indices.copy()

    def get_index_count(self):
        return len(self.__indices)

    def bind_vba(self):
        self.__vba.bind()

    def unbind_vba(self):
        self.__vba.unbind()


class RenderableObject(BaseTransform):
    def __init__(self):
        super(RenderableObject, self).__init__()
        self.mesh = None
        self.shader_program = None

    def render(self, camera):
        model = glm.translate(self.translation) * glm.mat4_cast(self.rotation) * glm.scale(self.scale)
        mvp = camera.get_proj_mat() * camera.get_view_mat() * model

        self.shader_program.use()
        self.shader_program.set_mat4("Instance.Model", model)
        self.shader_program.set_mat4("Instance.MVP", mvp)

        self.mesh.bind_vba()
        GL.glDrawElements(GL.GL_TRIANGLES, self.mesh.get_index_count(), GL.GL_UNSIGNED_INT, None)
        self.mesh.unbind_vba()


class Camera(BaseTransform):
    def __init__(self, width, height):
        super(Camera, self).__init__()
        self.translation = glm.vec3(0, 0, -1)
        self.rotation = glm.quat_cast(glm.rotate(glm.pi() / 8, glm.vec3(0, 1, 0)))
        self.fov = 60
        self.min_z = 0.01
        self.max_z = 100
        self.aspect = width / height

    def get_view_mat(self):
        return glm.lookAt(self.translation, self.translation + self.get_forward(), glm.vec3(0, 1, 0))

    def get_proj_mat(self):
        return glm.perspective(glm.radians(self.fov), self.aspect, self.min_z, self.max_z)


class CameraController:
    def __init__(self, camera):
        self.camera = camera
        self.move_speed = 0.1
        self.mouse_sensitivity = 0.003
        self.min_rotate_delta = 1

        self.__last_mouse_pos = glm.vec2()
        self.__mouse_rotating = False

    def handle_key_press(self, gl_widget, event):
        key = event.key()
        if key == Qt.Key_E:
            self.camera.move_by(0, self.move_speed, 0)
        if key == Qt.Key_Q:
            self.camera.move_by(0, -self.move_speed, 0)
        if key == Qt.Key_A:
            self.camera.move_by(self.move_speed, 0, 0)
        if key == Qt.Key_D:
            self.camera.move_by(-self.move_speed, 0, 0)
        if key == Qt.Key_W:
            self.camera.move_by(0, 0, self.move_speed)
        if key == Qt.Key_S:
            self.camera.move_by(0, 0, -self.move_speed)
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

        self.camera.rotate_by(-delta.y, delta.x, 0)
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


class Scene:
    def __init__(self):
        self.__objects: list[RenderableObject] = []
        self.camera = None

    def create_object(self) -> RenderableObject:
        obj = RenderableObject()
        self.__objects.append(obj)
        return obj

    def render(self):
        if not self.camera:
            return
        for obj in self.__objects:
            obj.render(self.camera)

    def unload(self):
        self.__objects.clear()
        self.camera = None