import glm


class Transform:
    def __init__(self):
        self.__translation = glm.vec3()
        self.__rotation = glm.quat()
        self.__scale = glm.vec3(1)
        self.__model_mat = glm.mat4(1)

    def _transform_changed(self):
        self.__recalculate_matrix()

    @property
    def translation(self) -> glm.vec3:
        return self.__translation

    @translation.setter
    def translation(self, value: glm.vec3):
        self.__translation = value
        self._transform_changed()

    @property
    def eulers(self) -> glm.vec3:
        return glm.eulerAngles(self.__rotation)

    @eulers.setter
    def eulers(self, value: glm.vec3):
        rotXMatrix = glm.rotate(value.x, glm.vec3(1, 0, 0))
        rotYMatrix = glm.rotate(value.y, glm.vec3(0, 1, 0))
        rotZMatrix = glm.rotate(value.z, glm.vec3(0, 0, 1))
        self.rotation = glm.quat_cast(rotZMatrix * rotYMatrix * rotXMatrix)

    @property
    def rotation(self) -> glm.quat:
        return self.__rotation

    @rotation.setter
    def rotation(self, value: glm.quat):
        self.__rotation = value
        self._transform_changed()

    @property
    def scale(self) -> glm.vec3:
        return self.__scale

    @scale.setter
    def scale(self, value: glm.vec3):
        self.__scale = value
        self._transform_changed()

    def rotate_by(self, value: glm.vec3):
        self.rotation *= glm.quat(value * glm.pi() / 180)

    def translate_by(self, value: glm.vec3):
        self.translation += value

    def move_by(self, move: glm.vec3):
        self.translation += move.x * self.right + move.y * self.up + move.z * self.forward

    @property
    def forward(self):
        return self.rotation * glm.vec3(0, 0, 1)

    @property
    def right(self):
        return self.rotation * glm.vec3(1, 0, 0)

    @property
    def up(self):
        return self.rotation * glm.vec3(0, 1, 0)

    def __recalculate_matrix(self):
        self.__model_mat = (glm.translate(self.translation) *
                            glm.mat4_cast(self.rotation) *
                            glm.scale(self.scale))

    @property
    def model_matrix(self):
        return self.__model_mat
