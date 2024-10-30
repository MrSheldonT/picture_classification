from enum import Enum

class Table(Enum):
    album = 'album'
    category = 'category'
    location = 'location'
    picture = 'picture'
    project = 'project'
    rating = 'rating'
    tag = 'tag'
    user = 'user'

class Transaccion(Enum):
    UPDATE = 'UPDATE'
    DELETE = 'DELETE'
    CREATE = 'CREATE'
    REQUEST = 'REQUEST'
    OTHERS = 'OTHERS'

class StatusResponse(Enum):
    SUCCESS = 'success'
    ERROR = 'error'

from app.extensions import mysql
from utils.audit import Table, Transaccion, StatusResponse


def register_audit(type_: Transaccion, request: str, message:str, status: StatusResponse, user_id: int, entity: Table):
    cursor = None
    try:
        cursor = mysql.connection.cursor()
        query = """
                    INSERT INTO
                        audit(type, request, message, status, user_id, entity)
                    VALUES
                        (%s, %s, %s, %s, %s, %s)
                """
        cursor.execute(query, (type_.value, request, message, status.value, user_id, entity.value))
        mysql.connection.commit()
    except Exception as e:
        print(f"Error during audit logging: {str(e)}")
    finally:
        if cursor:
            cursor.close()
