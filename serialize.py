import json
from Base_geometry_objects import *
from scenes import *
from generator_of_decoding_objects import generate_object_by_deserialized_data


def serialize(scene, file_name):
    """Сохраняет текущую сцену в json файл"""
    file = open(f"{file_name}.json", "w")
    objects = scene.get_objects()
    data = dict()
    for obj in objects:
        data.update(obj.get_serializing_dict())
    json.dump(data, file)
    close(file)

def deserialize(file_name):
    """По json файлу возвращает список объектов сцены"""
    file = open(f"{file_name}.json", "r")
    data = json.load(file)
    objects = list()
    for id in data.keys():
        objects.append(generate_object_by_deserialized_data(id, data[id], data))
    return objects

if __name__ == "__main__":
    pass