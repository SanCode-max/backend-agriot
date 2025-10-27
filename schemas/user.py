from bson import ObjectId

def userEntity(item) -> dict:
    return{
        "nombre": item["nombre"],
        "apellido": item["apellido"],
        "telefono": item["telefono"],
        "correo": item["correo"],
        "password": item["password"]
    }

def listUser(entity) -> list:
    return [listUser(item) for item in entity]

