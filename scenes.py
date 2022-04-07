import OpenGL.GL
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

    def get_model_mat(self):
        return glm.translate(self.translation) * glm.mat4_cast(self.rotation) * glm.scale(self.scale)


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


class SceneObject(BaseTransform):
    def __init__(self):
        super(SceneObject, self).__init__()
        self.mesh = None
        self.shader_program = None
        self.render_mode = GL.GL_TRIANGLES

    def get_render_mat(self, camera):
        return camera.get_mvp(self.get_model_mat())

    def render(self, camera):
        mvp = self.get_render_mat(camera)

        self.shader_program.use()
        self.shader_program.set_mat4("Instance.MVP", mvp)

        self.mesh.bind_vba()
        GL.glDrawElements(self.render_mode, self.mesh.get_index_count(), GL.GL_UNSIGNED_INT, None)
        self.mesh.unbind_vba()


class Camera(BaseTransform):
    default_position = glm.vec3(0, 0, -5)

    def __init__(self, width, height):
        super(Camera, self).__init__()
        self.translation = self.default_position
        self.fov = 60
        self.min_z = 0.01
        self.max_z = 100
        self.width = width
        self.height = height

    def get_view_mat(self):
        return glm.lookAt(self.translation, self.translation + self.get_forward(), glm.vec3(0, 1, 0))

    def get_proj_mat(self):
        return glm.perspective(glm.radians(self.fov), self.width / self.height, self.min_z, self.max_z)

    def get_mvp(self, model_mat):
        return self.get_proj_mat() * self.get_view_mat() * model_mat

    def to_screen_space(self, vec3):
        device_space = self.to_device_space_2d(vec3)
        if not device_space:
            return None
        return ((device_space + 1) / 2) * glm.vec2(self.width, self.height)

    def to_device_space_2d(self, vec3):
        clip_space = self.get_proj_mat() * (self.get_view_mat() * glm.vec4(vec3, 1))
        if abs(clip_space.w) < 1e-8:
            return None
        device_space = glm.vec3(clip_space.x, clip_space.y, clip_space.z) / clip_space.w
        return glm.vec2(device_space)


class CameraController:
    def __init__(self, camera):
        self.camera = camera
        self.move_speed = 0.1
        self.mouse_sensitivity = 0.003
        self.min_rotate_delta = 1

        self.__active_rendering_mode = 0
        self.__rendering_modes = [OpenGL.GL.GL_FILL, OpenGL.GL.GL_LINE, OpenGL.GL.GL_POINT]

        self.__last_mouse_pos = glm.vec2()
        self.__mouse_rotating = False

    def handle_key_press(self, gl_widget, event):
        key = event.key()
        match key:
            case Qt.Key_F:
                self.__active_rendering_mode = (self.__active_rendering_mode + 1) % len(self.__rendering_modes)
                OpenGL.GL.glPolygonMode(OpenGL.GL.GL_FRONT_AND_BACK, self.__rendering_modes[self.__active_rendering_mode])
            case Qt.Key_R:
                self.camera.rotation = glm.quat()
                self.camera.translation = self.camera.default_position
            case Qt.Key_E:
                self.camera.translate_by(0, self.move_speed, 0)
            case Qt.Key_Q:
                self.camera.translate_by(0, -self.move_speed, 0)
            case Qt.Key_A:
                self.camera.move_by(self.move_speed, 0, 0)
            case Qt.Key_D:
                self.camera.move_by(-self.move_speed, 0, 0)
            case Qt.Key_W:
                self.camera.move_by(0, 0, self.move_speed)
            case Qt.Key_S:
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
        self.__objects: list[SceneObject] = []
        self.camera = None

    @staticmethod
    def load_from_file(filename):
        try:
            with open(filename) as f:
                pass
        except OSError as e:
            print(e)
            exit(1)

    def add_object(self, obj):
        self.__objects.append(obj)

    def remove_object(self, obj):
        self.__objects.remove(obj)

    def render(self):
        if not self.camera:
            return
        for obj in self.__objects:
            obj.render(self.camera)

    def unload(self):
        self.__objects.clear()
        self.camera = None
