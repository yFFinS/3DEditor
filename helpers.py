import numpy as np


def to_float32_array(array):
    return np.array(array, dtype=np.float32)


def to_uint32_array(array):
    return np.array(array, dtype=np.uint32)


def as_uint32_array(value):
    return to_uint32_array([value])


def empty_float32_array():
    return np.array([], dtype=np.float32)


def empty_uint32_array():
    return np.array([], dtype=np.uint32)