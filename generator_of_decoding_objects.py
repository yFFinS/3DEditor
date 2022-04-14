from Base_geometry_objects import *

def generate_object_by_deserialized_data(id, data, all_objects_data):
    """Генерирует объект по декодированному словарю json"""
    if data["type"] == "point":
        return Point(name=data["name"],
                     id=id,
                     x=data["forming objects"][0],
                     y=data["forming objects"][1],
                     z=data["forming objects"][1])
    elif data["type"] == "line":
        if data["forming objects"][1].type == "line":
            return LineByPointAndLine(id=id,
                                      name=data["name"],
                                      point=generate_object_by_deserialized_data(data["forming objects"][0],
                                                                                 all_objects_data[data["forming objects"][0]],
                                                                                 all_objects_data),
                                      line=generate_object_by_deserialized_data(data["forming objects"][1],
                                                                                all_objects_data[data["forming objects"][1]],
                                                                                all_objects_data)
                                      )
        else:
            return LineBy2Points(id=id,
                                 name=data["name"],
                                 point1=generate_object_by_deserialized_data(data["forming objects"][0],
                                                                             all_objects_data[data["forming objects"][0]],
                                                                             all_objects_data),
                                 point2=generate_object_by_deserialized_data(data["forming objects"][1],
                                                                             all_objects_data[data["forming objects"][1]],
                                                                             all_objects_data)
                                 )
    elif data["type"] == "plane":
        if data["forming objects"][1].type == "plane":
            return PlaneByPointAndPlane(id=id,
                                        name=data["name"],
                                        point=generate_object_by_deserialized_data(data["forming objects"][0],
                                                                                   all_objects_data[data["forming objects"][0]],
                                                                                   all_objects_data),
                                        plane=generate_object_by_deserialized_data(data["forming objects"][1],
                                                                                   all_objects_data[data["forming objects"][1]],
                                                                                   all_objects_data)
                                        )
        else:
            return PlaneBy3Points(id=id,
                                  name=data["name"],
                                  point1=generate_object_by_deserialized_data(data["forming objects"][0],
                                                                             all_objects_data[
                                                                                 data["forming objects"][0]],
                                                                             all_objects_data),
                                  point2=generate_object_by_deserialized_data(data["forming objects"][1],
                                                                             all_objects_data[
                                                                                 data["forming objects"][1]],
                                                                             all_objects_data),
                                  point3=generate_object_by_deserialized_data(data["forming objects"][2],
                                                                             all_objects_data[
                                                                                 data["forming objects"][2]],
                                                                             all_objects_data)
                                  )
    elif data["type"] == "segment":
        return Segment(id=id,
                       name=data["name"],
                       point1=generate_object_by_deserialized_data(data["forming objects"][0],
                                                                  all_objects_data[data["forming objects"][0]],
                                                                  all_objects_data),
                       point2=generate_object_by_deserialized_data(data["forming objects"][0],
                                                                  all_objects_data[data["forming objects"][0]],
                                                                  all_objects_data)
                       )
    elif data["type"] == "base_3d_object":
        return BaseVolumetricBody(id=id,
                                  name=data["name"],
                                  points=[generate_object_by_deserialized_data(data["forming objects"][i],
                                                                               all_objects_data[data["forming objects"][i]],
                                                                               all_objects_data)
                                          for i in range(len(data["forming objects"]))]
                                  )
    else:
        raise Exception("Unexpected object type")