import abc
from abc import ABC, ABCMeta

from PyQt5.QtGui import QMouseEvent

from core.interfaces import UpdateReceiverInterface
from scene.scene import *
from scene.scene_object import SceneObject


class SceneActionsInterface:
    def action_move(self):
        raise NotImplementedError

    def action_point(self):
        raise NotImplementedError

    def action_line(self):
        raise NotImplementedError

    def action_plane(self):
        raise NotImplementedError


class GLSceneInterface:
    on_scene_changed: Event

    def get_scene(self) -> Scene:
        raise NotImplementedError

    def redraw(self):
        raise NotImplementedError

    def unload(self):
        raise NotImplementedError

    def no_action(self):
        raise NotImplementedError

    def move_object(self):
        raise NotImplementedError

    def create_point(self):
        raise NotImplementedError

    def create_line(self):
        raise NotImplementedError

    def create_plane(self):
        raise NotImplementedError

    def create_edge(self):
        raise NotImplementedError

    def create_face(self):
        raise NotImplementedError

    def create_rect(self):
        raise NotImplementedError

    def try_select_scene_object(self, event: QMouseEvent) -> bool:
        raise NotImplementedError


class SceneExplorerInterface:
    @abc.abstractmethod
    def add_scene_object(self, scene_object: SceneObject):
        raise NotImplementedError

    @abc.abstractmethod
    def clear_selection(self):
        raise NotImplementedError

    @abc.abstractmethod
    def select_scene_object(self, scene_object: SceneObject,
                            deselect_others: bool = False):
        raise NotImplementedError

    @abc.abstractmethod
    def deselect_scene_object(self, scene_object: SceneObject):
        raise NotImplementedError
