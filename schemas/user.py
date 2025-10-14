def userEntity(item) -> dict:
    return{
        "id": item["id"],
        "nombre": item["nombre"],
        "apellido": item["apellido"],
        "telefono": item["telefono"],
        "correo": item["correo"],
        "contraseña": item["contraseña"]
    }

def listUser(entity) -> list:
    [listUser(item) for item in entity]