import glm
import numpy

from native_rendering import *


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
        return glm.translate(self.translation) * \
               glm.mat4_cast(self.rotation) * \
               glm.scale(self.scale)


class SceneObject(BaseTransform):
    default_shader_program = None

    def __init__(self):
        super(SceneObject, self).__init__()
        self.mesh = None
        self.shader_program = self.default_shader_program
        self.render_mode = GL.GL_TRIANGLES
        self.selected = False

    def get_render_mat(self, camera):
        return camera.get_mvp(self.get_model_mat())

    def get_selection_mask(self):
        return 0

    def set_position(self, x, y, z):
        self.translation = glm.vec3(x, y, z)

    def get_selection_weight(self, camera, x, y):
        """
            Возвращает значение от 0 до 1. Чем больше, тем больше приоритет выбора этого объекта.
            Возвращает None если оьъект выбирать не нужно.
        """
        return None

    def render(self, camera):
        mvp = self.get_render_mat(camera)

        self.shader_program.use()
        self.shader_program.set_mat4("Instance.MVP", mvp)
        self.shader_program.set_float("Instance.Selected", 1 if self.selected else -1)

        self.mesh.bind_vba()
        GL.glDrawElements(self.render_mode, self.mesh.get_index_count(), GL.GL_UNSIGNED_INT, None)
        self.mesh.unbind_vba()


class Scene:
    def __init__(self):
        self.__objects = []
        self.camera = None

    @staticmethod
    def load_from_file(filename):
        try:
            with open(filename) as f:
                pass
        except OSError as e:
            print(e)
            exit(1)

    def get_objects(self):
        return self.__objects

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

    def try_select_object(self, x, y, mask=0xFFFFFFFF):
        to_select = None
        select_w = -1
        for obj in self.get_objects():
            if obj.selected or (mask & obj.get_selection_mask()) == 0:
                continue
            weight = obj.get_selection_weight(self.camera, x, self.camera.height - y)
            if weight is None:
                continue
            if weight < 0 or weight > 1:
                raise ValueError(f"Вес должен быть от 0 до 1. Был {weight}.")
            if weight > select_w:
                select_w = weight
                to_select = obj
        return to_select
