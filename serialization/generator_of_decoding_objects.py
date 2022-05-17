from core.Base_geometry_objects import *


def generate_object_by_deserialized_data(obj_id, data, generated_objects):
    """Генерирует объект по декодированному словарю json"""

    def get_from_id(req_id):
        generate_object_by_deserialized_data(req_id, data, generated_objects)
        return generated_objects[req_id]

    if obj_id in generated_objects:
        return

    res = None

    obj_data = data[obj_id]
    obj_type = obj_data["type"]
    forming_objects = obj_data["forming objects"]
    obj_name = obj_data["name"]

    if obj_type == "point":
        pos = glm.vec3(forming_objects[0], forming_objects[1], forming_objects[2])
        res = Point(pos=pos, name=obj_name, id=obj_id)
        generated_objects[obj_id] = res
        return

    forming_objects = [get_from_id(req_id) for req_id in forming_objects]

    if obj_type == "line":
        f1, f2 = forming_objects
        if f2.type == "line":
            res = LineByPointAndLine(id=obj_id,
                                     name=obj_name,
                                     point=f1,
                                     line=f2
                                     )
        else:
            res = LineBy2Points(id=obj_id,
                                name=obj_name,
                                point1=f1,
                                point2=f2
                                )
    elif obj_type == "plane":
        f1, f2, *_ = forming_objects
        if f2.type == "plane":
            res = PlaneByPointAndPlane(id=obj_id,
                                       name=obj_name,
                                       point=f1,
                                       plane=f2
                                       )
        elif f2.type == "line":
            res = PlaneByPointAndLine(id=obj_id,
                                      name=obj_name,
                                      point=f1,
                                      line=f2
                                      )
        elif f2.type == "segment":
            res = PlaneByPointAndSegment(id=obj_id,
                                         name=obj_name,
                                         point=f1,
                                         segment=f2
                                         )
        else:
            res = PlaneBy3Points(id=obj_id,
                                 name=obj_name,
                                 point1=f1,
                                 point2=f2,
                                 point3=forming_objects[2]
                                 )
    elif obj_type == "segment":
        res = Segment(id=obj_id,
                      name=obj_name,
                      point1=forming_objects[0],
                      point2=forming_objects[1]
                      )
    elif obj_type == "triangle":
        res = Triangle(id=obj_id,
                       name=obj_name,
                       point1=forming_objects[0],
                       point2=forming_objects[1],
                       point3=forming_objects[2],
                       )
    elif obj_type == "base_3d_object":
        res = BaseVolumetricBody(id=obj_id,
                                 name=obj_name,
                                 points=forming_objects
                                 )
    else:
        print(f"Unknown object type {obj_type}")

    if res is None:
        print(f"Unknown object type {obj_type}")
    else:
        generated_objects[obj_id] = res
