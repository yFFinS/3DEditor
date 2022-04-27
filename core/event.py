from typing import Callable


class Event:
    def __init__(self):
        self.__listeners = []

    def __iadd__(self, other: Callable) -> 'Event':
        self.__listeners.append(other)
        return self

    def __isub__(self, other: Callable) -> 'Event':
        self.__listeners.remove(other)
        return self

    def invoke(self, *args, **kwargs):
        for listener in self.__listeners:
            listener(*args, **kwargs)
