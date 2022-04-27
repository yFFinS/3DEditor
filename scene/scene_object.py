import glm
import numpy as np
from OpenGL import GL

from scene.camera import Camera
from render.mesh import Mesh
from scene.transform import Transform


class SceneObject:
    SHADER_PROGRAM = None

    def __init__(self):
        self.transform = Transform()

        self.mesh = Mesh()
        self.shader_program = SceneObject.SHADER_PROGRAM
        self.render_mode = GL.GL_TRIANGLES
        self.selected = False
        self.render_layer = 0
        self.selection_mask = 0

    def get_render_mat(self, camera: Camera) -> glm.mat4:
        return camera.get_mvp(self.transform.model_matrix)

    def set_position(self, pos: glm.vec3):
        self.transform.translation = pos

    def get_selection_weight(self, camera: Camera, click_pos: glm.vec2) -> float:
        """
            Возвращает значение от 0 до 1. Чем больше значение, тем больше приоритет выбора этого объекта.
            Возвращает NaN, если объект выбирать не нужно.
        """
        return np.nan

    def render(self, camera: Camera):
        mvp = self.get_render_mat(camera)

        self.shader_program.use()
        self.shader_program.set_mat4("Instance.MVP", mvp)
        self.shader_program.set_float("Instance.Selected", 1 if self.selected else -1)

        self.mesh.bind_vba()
        indices = self.mesh.get_index_count()
        if indices != 0:
            GL.glDrawElements(self.render_mode, indices, GL.GL_UNSIGNED_INT, None)
        else:
            GL.glDrawArrays(self.render_mode, 0, self.mesh.get_vertex_count())
        self.mesh.unbind_vba()
