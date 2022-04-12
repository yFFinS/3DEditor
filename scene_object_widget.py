from render_geometry import *
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel


class SceneObjectWidget(QWidget):
    __point_counter = 1
    __line_counter = 1
    __plane_counter = 1

    def __init__(self, scene_object):
        super(SceneObjectWidget, self).__init__()
        self.__layout = QHBoxLayout()

        font = QFont("Arial", 14)
        self.__name_label = QLabel(self)
        self.__name_label.setFont(font)

        if isinstance(scene_object, ScenePoint):
            text = f'Point{SceneObjectWidget.__point_counter}'
            SceneObjectWidget.__point_counter += 1
        elif isinstance(scene_object, SceneLine):
            text = f'Line{SceneObjectWidget.__line_counter}'
            SceneObjectWidget.__line_counter += 1
        elif isinstance(scene_object, ScenePlane):
            text = f'Plane{SceneObjectWidget.__plane_counter}'
            SceneObjectWidget.__plane_counter += 1
        else:
            text = 'Unknown'

        self.__name_label.setText(text)
        self.__layout.addWidget(self.__name_label)
        self.__scene_object = scene_object

        self.__layout.addStretch()
        self.setLayout(self.__layout)

    def get_object(self):
        return self.__scene_object

    def sizeHint(self):
        return self.__layout.sizeHint()
