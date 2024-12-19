from app.extensions import mysql

def exist_record_in_table(table, parameter, value):
    
    cursor = None
    try:
        cursor = mysql.connection.cursor()
        query = f"SELECT * FROM {table} WHERE {parameter} = %s"
        cursor.execute(query, (value, ))
        response = cursor.fetchone()
        cursor.close()
        return response is not None

    except Exception as e:
        return str(e)
    finally:
        if cursor:
            cursor.close()

