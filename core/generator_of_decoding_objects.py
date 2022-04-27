from core.Base_geometry_objects import *

def generate_object_by_deserialized_data(id, data, all_objects_data, generated_objects):
    """Генерирует объект по декодированному словарю json"""

    if id in generated_objects:
        return generated_objects[id]

    if data["type"] == "point":
        res = Point(name=data["name"],
                     id=id,
                     x=data["forming objects"][0],
                     y=data["forming objects"][1],
                     z=data["forming objects"][1])
        generated_objects[id] = res
        return res
    elif data["type"] == "line":
        if data["forming objects"][1].type == "line":
            res = LineByPointAndLine(id=id,
                                      name=data["name"],
                                      point=generate_object_by_deserialized_data(data["forming objects"][0],
                                                                                 all_objects_data[data["forming objects"][0]],
                                                                                 all_objects_data,
                                                                                 generated_objects),
                                      line=generate_object_by_deserialized_data(data["forming objects"][1],
                                                                                all_objects_data[data["forming objects"][1]],
                                                                                all_objects_data,
                                                                                generated_objects)
                                      )
            generated_objects[id] = res
            return res
        else:
            res = LineBy2Points(id=id,
                                 name=data["name"],
                                 point1=generate_object_by_deserialized_data(data["forming objects"][0],
                                                                             all_objects_data[data["forming objects"][0]],
                                                                             all_objects_data,
                                                                             generated_objects),
                                 point2=generate_object_by_deserialized_data(data["forming objects"][1],
                                                                             all_objects_data[data["forming objects"][1]],
                                                                             all_objects_data,
                                                                             generated_objects)
                                 )
            generated_objects[id] = res
            return res
    elif data["type"] == "plane":
        if data["forming objects"][1].type == "plane":
            res = PlaneByPointAndPlane(id=id,
                                        name=data["name"],
                                        point=generate_object_by_deserialized_data(data["forming objects"][0],
                                                                                   all_objects_data[data["forming objects"][0]],
                                                                                   all_objects_data,
                                                                                   generated_objects),
                                        plane=generate_object_by_deserialized_data(data["forming objects"][1],
                                                                                   all_objects_data[data["forming objects"][1]],
                                                                                   all_objects_data,
                                                                                   generated_objects)
                                        )
            generated_objects[id] = res
            return res
        else:
            res = PlaneBy3Points(id=id,
                                  name=data["name"],
                                  point1=generate_object_by_deserialized_data(data["forming objects"][0],
                                                                             all_objects_data[
                                                                                data["forming objects"][0]],
                                                                             all_objects_data,
                                                                              generated_objects),
                                  point2=generate_object_by_deserialized_data(data["forming objects"][1],
                                                                             all_objects_data[
                                                                                 data["forming objects"][1]],
                                                                             all_objects_data,
                                                                             generated_objects),
                                  point3=generate_object_by_deserialized_data(data["forming objects"][2],
                                                                             all_objects_data[
                                                                                 data["forming objects"][2]],
                                                                             all_objects_data,
                                                                             generated_objects)
                                  )
            generated_objects[id] = res
            return res
    elif data["type"] == "segment":
        res = Segment(id=id,
                       name=data["name"],
                       point1=generate_object_by_deserialized_data(data["forming objects"][0],
                                                                  all_objects_data[data["forming objects"][0]],
                                                                  all_objects_data),
                       point2=generate_object_by_deserialized_data(data["forming objects"][0],
                                                                  all_objects_data[data["forming objects"][0]],
                                                                  all_objects_data)
                       )
        generated_objects[id] = res
        return res
    elif data["type"] == "base_3d_object":
        res = BaseVolumetricBody(id=id,
                                  name=data["name"],
                                  points=[generate_object_by_deserialized_data(data["forming objects"][i],
                                                                               all_objects_data[data["forming objects"][i]],
                                                                               all_objects_data)
                                          for i in range(len(data["forming objects"]))]
                                  )
        generated_objects[id] = res
        return res
    else:
        raise Exception("Unexpected object type")