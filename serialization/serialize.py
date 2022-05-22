import json

import glm

from scene.camera import Camera
from scene.scene import Scene
from scene.scene_object import SceneObject
from serialization.generator_of_decoding_objects import \
    generate_object_by_deserialized_data


def extract_camera_settings(camera: Camera):
    pos = camera.translation
    rot = camera.rotation
    return {
        "translation": f"{pos.x} {pos.y} {pos.z}",
        "rotation": f"{rot.w} {rot.x} {rot.y} {rot.z}",
    }


def inject_camera_settings(camera: Camera, settings: dict[str, str]):
    pos = glm.vec3(*[float(value) for value in settings["translation"].split()])
    rot = glm.quat(*[float(value) for value in settings["rotation"].split()])
    glm.vec2()
    camera.translation = pos
    camera.rotation = rot


def extract_children(destination, scene_object):
    obj_id = scene_object.id
    if obj_id not in destination:
        destination[obj_id] = []
    destination[obj_id].extend(
        [child.id for child in scene_object.children])


def serialize_scene(scene: Scene, file_name: str):
    serialized_objects = {}
    children = {}

    for obj in scene.objects:
        extract_children(children, obj)
        primitive = obj.primitive
        if primitive is None:
            print(
                f"Scene object name: {obj.name} id: {obj.id} has no primitive")
            continue
        serialized_obj = primitive.get_serializing_dict()
        serialized_objects.update(serialized_obj)

    data = {
        "camera": extract_camera_settings(scene.camera),
        "objects": serialized_objects,
        "children": children
    }

    with open(file_name, "w") as file:
        json.dump(data, file)

def deserialize_scene(file_name: str) -> (
        dict[str, str], dict[str, SceneObject]):
    with open(file_name, "r") as file:
        data = json.load(file)

    objects = dict()

    camera_settings = data["camera"]
    object_data = data["objects"]
    children_data = data["children"]

    for obj_id in object_data:
        generate_object_by_deserialized_data(obj_id, object_data, objects)

    return camera_settings, objects, children_data
