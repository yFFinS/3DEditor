from abc import ABC

from PyQt5.QtCore import QEvent
from PyQt5.QtGui import QMouseEvent, QWheelEvent, QKeyEvent


class UpdateReceiverInterface:
    def update(self):
        raise NotImplementedError


class EventHandlerInterface:
    def on_any_event(self, event: QEvent):
        pass

    def on_mouse_move(self, event: QMouseEvent):
        pass

    def on_mouse_pressed(self, event: QMouseEvent):
        pass

    def on_mouse_released(self, event: QMouseEvent):
        pass

    def on_wheel_scroll(self, event: QWheelEvent):
        pass

    def on_key_pressed(self, event: QKeyEvent):
        pass

    def on_key_released(self, event: QKeyEvent):
        pass
