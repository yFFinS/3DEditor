from PyQt5.QtCore import QEvent
from PyQt5.QtGui import QWheelEvent, QMouseEvent, QKeyEvent

from core.interfaces import EventHandlerInterface


def dispatch(handler: EventHandlerInterface, event: QEvent) -> bool:
    res = None
    handler.on_any_event(event)
    match event.type():
        case QEvent.Wheel:
            event = QWheelEvent(event)
            res = handler.on_wheel_scroll(event)
        case QEvent.MouseButtonPress:
            event = QMouseEvent(event)
            res = handler.on_mouse_pressed(event)
        case QEvent.MouseButtonDblClick:
            event = QMouseEvent(event)
            res = handler.on_mouse_double_click(event)
        case QEvent.MouseButtonRelease:
            event = QMouseEvent(event)
            res = handler.on_mouse_released(event)
        case QEvent.MouseMove:
            event = QMouseEvent(event)
            res = handler.on_mouse_move(event)
        case QEvent.KeyPress:
            event = QKeyEvent(event)
            res = handler.on_key_pressed(event)
        case QEvent.KeyRelease:
            event = QKeyEvent(event)
            res = handler.on_key_released(event)
    return bool(res)
