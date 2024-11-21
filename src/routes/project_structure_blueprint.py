from flask import Blueprint, jsonify, request
from utils.token_validation import token_required
from app.extensions import mysql
from datetime import datetime
from utils.validate_data import valid_date
from utils.database_verification import exist_record_in_table
from utils.message_status import Status
from utils.audit import register_audit, Transaccion, Table, StatusResponse

project_structure_bp = Blueprint('projects', __name__, url_prefix='/projects')

@project_structure_bp.route('/create_project', methods=['POST'])
@token_required
def create_project(token_data, original_token):

    project_name = request.form.get('project_name', type=str)
    project_description = request.form.get('project_description', type=str)
    project_date = request.form.get('project_date', type=str, default=datetime.today().strftime('%Y-%m-%d'))
    table = "project"
    parameter = "name"
    message_enpoint = ""
    status_response = ""

    if not project_name or not project_description or not project_date:
        return jsonify({'status': StatusResponse.ERROR.value, 'message' : Status.NOT_ENTERED.value, 'project_name' : project_name, 'project_description' : project_description, 'project_date' : project_date}), 400

    if exist_record_in_table(table, parameter, project_name):
        return jsonify({'status': StatusResponse.ERROR.value, 'message': 'The project name you are trying to register already exists!'}), 409

    cursor = None
    try:
        cursor = mysql.connection.cursor()
        
        query = """
                    INSERT INTO project(name, description, date) 
                    VALUES(%s,%s, %s)
                """
        cursor.execute(query,(project_name, project_description, project_date))
        mysql.connection.commit()
        message_enpoint = {'status': StatusResponse.SUCCESS.value, 'message': 'The project was saved correctly', 'project_name' : project_name, 'project_description' : project_description, 'project_date' : project_date}
        status_response = StatusResponse.SUCCESS
        return jsonify(message_enpoint), 200

    except ValueError as ve:
        message_enpoint = {'status': StatusResponse.ERROR.value, 'message': 'Incorrect date format', StatusResponse.ERROR.value: str(ve)}
        status_response = StatusResponse.ERROR
        return jsonify(message_enpoint), 400
    
    except Exception as e:
        message_enpoint = {'status': StatusResponse.ERROR.value, 'message': str(e) }
        status_response = StatusResponse.ERROR
        return jsonify(message_enpoint), 500

    finally:
        if cursor:
            cursor.close()
        print()
        register_audit(
                type_=Transaccion.CREATE, 
                request=request.url,
                message= message_enpoint,
                status= status_response,
                user_id=token_data['user_id'], 
                entity=Table.project
        )

@project_structure_bp.route('/show_projects',methods=['GET'])
@token_required
def show_projects(token_data, original_token):

    page = request.args.get('page', default=1, type=int)
    quantity = request.args.get('quantity', default=50, type=int)
    offset = ( page - 1 ) * quantity
    
    cursor = None    
    try:
        cursor = mysql.connection.cursor() 
        query = """
                    SELECT 
                        project_id, name, description, date 
                    FROM 
                        project
                    LIMIT %s 
                    OFFSET %s
                """
        cursor.execute(query,(quantity, offset))
        response = cursor.fetchall()
        
        return jsonify({'status': StatusResponse.SUCCESS.value, 'message' : Status.SUCCESSFULLY_CONSULTED.value, 'response' : response}), 200
    
    except Exception as e:
        return jsonify({'status': StatusResponse.ERROR.value, 'message' : str(e) }), 500
    
    finally:
        if cursor:
            cursor.close()

@project_structure_bp.route('/update_project', methods=['PATCH'])
@token_required
def update_project(token_data, original_token):
    
    project_id = request.form.get('project_id', type=int)
    project_name = request.form.get('project_name', type=str)
    project_description = request.form.get('project_description', type=str)
    project_date = valid_date(request.form.get('project_date', type=str, default=datetime.today().strftime('%Y-%m-%d')))
    status_response = ""
    message_enpoint = ""
    table = "project"
    parameter = "name"

    if project_date is None:
        return jsonify({'status': StatusResponse.ERROR.value, 'message': 'Invalid date format. Use YYYY-MM-DD'}), 400

    if not project_id or not project_name or    not project_description or not project_date:
        return jsonify({'message' : Status.NOT_ENTERED.value, 'project_id' : project_id, 'project_name' : project_name, 'project_description' : project_description, 'project_date' : project_date}), 400

    if exist_record_in_table(table, parameter, project_name):
        return jsonify({'status': StatusResponse.ERROR.value, 'message': 'The project name you are trying to register already exists!'}), 409

    cursor = None
    try:
        cursor = mysql.connection.cursor()
        query = """
                    UPDATE 
                        project   
                    SET 
                        name = %s, description = %s, date = %s
                    WHERE 
                        project_id = %s 
                """
        cursor.execute(query,(project_name, project_description, project_date, project_id))
        mysql.connection.commit()
        status_response = StatusResponse.SUCCESS
        message_enpoint = {'status': StatusResponse.SUCCESS.value, 'message' : Status.SUCCESSFULLY_UPDATED.value}

        return jsonify(message_enpoint), 200
    
    except Exception as e:
        status_response = StatusResponse.ERROR
        message_enpoint = {'status': StatusResponse.ERROR.value, 'message' : str(e) }

        return jsonify(message_enpoint), 500
    
    finally:
        if cursor:
            cursor.close()
        register_audit(
                type_=Transaccion.UPDATE, 
                request=request.url,
                message=message_enpoint,
                status=status_response,
                user_id=token_data['user_id'], 
                entity=Table.project
        )


@project_structure_bp.route('/delete_project', methods = ['DELETE'])
@token_required
def delete_project(token_data, original_token):
    project_id = request.form.get('project_id', type=int)
    table = 'project'
    parameter = 'project_id'
    status_response = ""
    message_enpoint = ""

    if not project_id:
         return jsonify({'status': StatusResponse.ERROR.value, 'message' : Status.NOT_ENTERED.value, 'project_id' : project_id}), 400
    
    if  exist_record_in_table(table, parameter, project_id):
        return jsonify({'status': StatusResponse.ERROR.value, 'message' : Status.RECORD_NOT_FOUND.value}), 404
    
    cursor = None
    try:
        cursor = mysql.connection.cursor()
        query = """
                    DELETE FROM
                        project
                    WHERE
                        project_id = %s
                """

        cursor.execute(query, (project_id,))
        mysql.connection.commit()
        status_response = StatusResponse.SUCCESS
        message_enpoint = {'status': StatusResponse.SUCCESS.value, 'message' : Status.SUCCESSFULLY_DELETED.value, 'project_id': project_id}

        return jsonify(message_enpoint), 200                                                                    

    except Exception as e:
        status_response = StatusResponse.ERROR
        message_enpoint = {'status': StatusResponse.ERROR.value, 'message': str(e)}

        return jsonify(message_enpoint), 500
    
    finally:
        if cursor:
            cursor.close()
        register_audit(
                type_=Transaccion.DELETE, 
                request=request.url,
                message=message_enpoint,
                status=status_response,
                user_id=token_data['user_id'], 
                entity=Table.project
        )

@project_structure_bp.route('/create_location', methods=['POST']) 
@token_required
def create_location(token_data, original_token):

    location_name = request.form.get('location_name', type=str)
    location_coordinates = request.form.get('location_coordinates', type=str, default="No documentado")
    project_id = request.form.get('project_id', type=int)
    table = "location"
    parameter = "name"
    status_response = ""
    message_enpoint = ""

    if exist_record_in_table(table, parameter, location_name):
        return jsonify({'status': StatusResponse.ERROR.value, 'message': 'The location name you are trying to register already exists!'}), 409

    if not exist_record_in_table("project", "project_id", project_id):
        return jsonify({'status': StatusResponse.ERROR.value, 'message': 'The project where you are trying to register the location does not exist!'}), 409
    
    cursor = None
    try:
        cursor = mysql.connection.cursor()
        query = """
                    INSERT INTO location(name, coordinates, project_id)
                    VALUES(%s,%s,%s)
                """
        cursor.execute(query,(location_name, location_coordinates, project_id))   
        mysql.connection.commit()
        status_response = StatusResponse.SUCCESS
        message_enpoint = {'status' : StatusResponse.SUCCESS.value, 'message': 'Record was saved correctly', 'location_name' : location_name, 'location_coordinates':location_coordinates, 'project_id':project_id}

        return jsonify(message_enpoint), 200
    
    except Exception as e:
        status_response = StatusResponse.ERROR
        message_enpoint = {'status' : StatusResponse.ERROR.value, 'message': str(e) }

        return jsonify(message_enpoint), 500
    
    finally:
        if cursor:
            cursor.close()
        register_audit(
                type_=Transaccion.CREATE, 
                request=request.url,
                message=message_enpoint,
                status=status_response,
                user_id=token_data['user_id'], 
                entity=Table.location
        )

@project_structure_bp.route('/show_locations', methods=['GET'])
@token_required
def show_locations(token_data, original_token):
    
    project_id = request.args.get('project_id', type=int)  
    page = request.args.get('page', default=1, type=int)
    quantity = request.args.get('quantity', default=50, type=int)
    offset = (page - 1) * quantity

    if not project_id:
        return jsonify({'status': StatusResponse.ERROR.value, 'message': Status.NOT_ENTERED.value, 'project_id': project_id})

    cursor = None
    try:
        cursor = mysql.connection.cursor()
        query = """
                    SELECT 
                        location_id, name, coordinates, project_id
                    FROM 
                        location
                    WHERE
                        project_id = %s
                    LIMIT %s
                    OFFSET %s
                """
        cursor.execute(query, (project_id, quantity, offset))
        response = cursor.fetchall()
        return jsonify({'status': StatusResponse.SUCCESS.value, 'message': Status.SUCCESSFULLY_CONSULTED.value, 'response': response}), 200
    
    except Exception as e:
        return jsonify({'status': StatusResponse.ERROR.value, 'message': str(e)}), 500
    
    finally:
        if cursor:
            cursor.close()

@project_structure_bp.route('/update_location', methods=['PATCH'])  #name location unique?
@token_required
def update_location(token_data, original_token):

    location_id = request.form.get('location_id', type=int)
    location_name = request.form.get('location_name', type=str)
    location_coordinates = request.form.get('location_coordinates', type=str, default="No documentado")
    project_id = request.form.get('project_id', type=int)
    table = "location"
    parameter = "location_id"
    status_response = ""
    message_enpoint = ""
    
    if not location_name or not location_coordinates or not location_id or not project_id:
        return jsonify({'message' : Status.NOT_ENTERED.value, 'project_id': project_id, 'location_name' : location_name, 'location_coordinates' : location_coordinates, 'location_id': location_id}), 400
   
    if not exist_record_in_table(table, parameter, location_id):
        return jsonify({'status': StatusResponse.ERROR.value, 'message' : Status.RECORD_NOT_FOUND.value}), 404
    
    cursor = None
    try:
        cursor = mysql.connection.cursor()
        query = """
                    UPDATE 
                        location
                    SET 
                        name = %s, coordinates = %s, project_id = %s
                    WHERE 
                        location_id = %s
                """
        cursor.execute(query,(location_name, location_coordinates, project_id, location_id ))
        mysql.connection.commit()
        status_response = StatusResponse.SUCCESS
        message_enpoint = {'status': StatusResponse.SUCCESS.value, 'message' : Status.SUCCESSFULLY_UPDATED.value}
    
        return jsonify(message_enpoint), 200
    
    except Exception as e:
        status_response = StatusResponse.SUCCESS
        message_enpoint = {'status': StatusResponse.ERROR.value, 'message' : str(e) }
    
        return jsonify(message_enpoint), 500
    
    finally:
        if cursor:
            cursor.close()
        register_audit(
                type_=Transaccion.UPDATE, 
                request=request.url,
                message=message_enpoint,
                status=status_response,
                user_id=token_data['user_id'], 
                entity=Table.location
        )

@project_structure_bp.route('/delete_location', methods=['DELETE'])
@token_required
def delete_location(token_data, original_token):
    location_id = request.form.get('location_id')
    table = 'location'
    parameter = 'location_id'
    status_response = ""
    message_enpoint = ""

    if not location_id:
         return jsonify({'status': StatusResponse.ERROR.value, 'message' : ' Parameters not entered', 'location_id' : location_id}), 400
    
    if not exist_record_in_table(table, parameter, location_id):
        return jsonify({'status': StatusResponse.ERROR.value, 'message' : Status.RECORD_NOT_FOUND.value}), 404
    
    cursor = None
    try:
        cursor = mysql.connection.cursor()
        query = """
                    DELETE FROM 
                        location
                    WHERE 
                        location_id = %s
                 """
        cursor.execute(query, (location_id, ))
        mysql.connection.commit()
        status_response = StatusResponse.SUCCESS
        message_enpoint = {'status': StatusResponse.SUCCESS.value, 'message' : Status.SUCCESSFULLY_DELETED.value}                                  
        
        return jsonify(message_enpoint), 200

    except Exception as e:
        status_response = StatusResponse.ERROR
        message_enpoint = {'status': StatusResponse.ERROR.value, 'message': str(e)}
        return jsonify(message_enpoint), 500
    
    finally:
        if cursor:
            cursor.close()
        register_audit(
                type_=Transaccion.DELETE, 
                request=request.url,
                message=message_enpoint,
                status=status_response,
                user_id=token_data['user_id'], 
                entity=Table.location
        )


@project_structure_bp.route('/create_album', methods=['POST'] )
@token_required
def create_album(token_data, original_token):

    location_id = request.form.get('location_id', type=int)
    album_name = request.form.get('album_name', type=str)
    album_date = request.form.get('album_date', type=str, default=datetime.today().strftime('%Y-%m-%d'))
    table = "album"
    parameter = "name"
    status_response = ""
    message_enpoint = ""

    if not location_id or not album_name or not album_date:
        return jsonify({'status' : StatusResponse.ERROR.value, 'message' : Status.NOT_ENTERED.value, 'location_id' : location_id, 'album_name' : album_name, 'album_date' : album_date}), 400
    
    if exist_record_in_table(table, parameter, album_name):
        return jsonify({'status': StatusResponse.ERROR.value, 'message': 'The album name you are trying to register already exists!'}), 409
    
    cursor = None
    try:
        cursor = mysql.connection.cursor()
        query = """
                    INSERT INTO album(name, date, location_id)
                    VALUES(%s,%s,%s)
                """
        cursor.execute(query, (album_name, album_date, location_id))
        mysql.connection.commit()
        status_response = StatusResponse.SUCCESS
        message_enpoint = {'status' : StatusResponse.SUCCESS.value, 'message': 'Record was saved correctly',  'location_id' : location_id, 'album_name' : album_name, 'album_date' : album_date }

        return jsonify(message_enpoint), 200
    
    except Exception as e:
        status_response = StatusResponse.ERROR
        message_enpoint = {'status' : StatusResponse.ERROR.value, 'message': str(e)}
        return jsonify(message_enpoint), 500
    
    finally:
        if cursor:
            cursor.close()
        register_audit(
                type_=Transaccion.CREATE, 
                request=request.url,
                message=message_enpoint,
                status=status_response,
                user_id=token_data['user_id'], 
                entity=Table.album
        )

@project_structure_bp.route('/show_albums', methods=['GET'])
@token_required
def show_albums(token_data, original_token):
    
    location_id = request.args.get('location_id', type=int)
    page = request.args.get('page', default=1, type=int)
    quantity = request.args.get('quantity', default=50, type=int)
    offset = ( page - 1 ) * quantity

    if not location_id:
        return jsonify({'status': StatusResponse.ERROR.value, 'message': Status.NOT_ENTERED.value, 'location_id': location_id}), 400

    cursor = None
    try:
        cursor = mysql.connection.cursor()
        query = """
                    SELECT 
                        album_id, location_id, name, date
                    FROM 
                        album
                    WHERE 
                        location_id = %s
                    LIMIT %s
                    OFFSET %s
                """
        cursor.execute(query, (location_id, quantity, offset))
        response = cursor.fetchall()
        return jsonify({'status': StatusResponse.SUCCESS.value, 'message' : Status.SUCCESSFULLY_CREATED.value, 'response' : response}), 200
    
    except Exception as e:
        return jsonify({'status': StatusResponse.ERROR.value, 'message' : str(e) }), 500
    
    finally:
        if cursor:
            cursor.close()
       

@project_structure_bp.route('/update_album', methods=['PATCH'])
@token_required
def update_album(token_data, original_token):
    album_id = request.form.get('album_id', type=int)
    album_name = request.form.get('album_name', type=str)
    location_id = request.form.get('location_id', type=int)
    album_date = request.form.get('album_date', type=str, default=datetime.today().strftime('%Y-%m-%d'))
    table = "album"
    parameter = "album_id"
    status_response = ""
    message_enpoint = ""

    if not album_id or not album_name or not location_id or not album_date:
        return jsonify({'status': StatusResponse.ERROR.value, 'message' : Status.NOT_ENTERED.value, 'album_id' : album_id, 'album_name' : album_name, 'location_id' : location_id, 'album_date' : album_date}), 400
    
    if not exist_record_in_table(table, parameter, album_id):
        return jsonify({'status': StatusResponse.ERROR.value, 'message' : Status.RECORD_NOT_FOUND.value}), 404
    
    cursor = None
    try:
        cursor = mysql.connection.cursor()
        query = """
                    UPDATE 
                        album
                    SET 
                        name = %s, date = %s, location_id = %s
                    WHERE 
                        album_id = %s
                """
        cursor.execute(query,(album_name, album_date, location_id, album_id))
        mysql.connection.commit()
        status_response = StatusResponse.SUCCESS
        message_enpoint = {'status': StatusResponse.SUCCESS.value, 'message' : Status.SUCCESSFULLY_UPDATED.value}
        
        return jsonify(message_enpoint), 200
    
    except Exception as e:
        status_response = StatusResponse.SUCCESS
        message_enpoint = {'status': StatusResponse.ERROR.value, 'message' : str(e) }
        return jsonify(message_enpoint), 500

    finally:
        if cursor:
            cursor.close()
        register_audit(
                type_=Transaccion.UPDATE, 
                request=request.url,
                message=message_enpoint,
                status=status_response,
                user_id=token_data['user_id'], 
                entity=Table.album
        )

@project_structure_bp.route('/delete_album', methods=['DELETE'])
@token_required
def delete_album(token_data, original_token):
    album_id = request.form.get('album_id', type=int)
    table = 'album'
    parameter = 'album_id'
    status_response = ""
    message_enpoint = ""

    if not album_id:
            return jsonify({'status': 'suerrorccess', 'message' : ' Parameters not entered', 'album_id' : album_id}), 400
    
    if not exist_record_in_table(table, parameter, album_id):
        return jsonify({'status': StatusResponse.ERROR.value, 'message' : Status.RECORD_NOT_FOUND.value}), 404
    
    cursor = None
    try:
        cursor =  mysql.connection.cursor()
        query  = """
                    DELETE FROM
                        album
                    WHERE 
                        album_id = %s
                 """
        cursor.execute(query, (album_id, ))
        mysql.connection.commit()

        status_response = StatusResponse.SUCCESS
        message_enpoint = {'status': StatusResponse.SUCCESS.value, 'message' : Status.SUCCESSFULLY_DELETED.value}
        
        return jsonify(message_enpoint), 200
    
    except Exception as e:
        status_response = StatusResponse.ERROR
        message_enpoint = {'status': StatusResponse.ERROR.value, 'message': str(e)}
        
        return jsonify(message_enpoint), 500
    
    finally:
        if cursor:
            cursor.close()
        register_audit(
                type_=Transaccion.DELETE, 
                request=request.url,
                message=message_enpoint,
                status=status_response,
                user_id=token_data['user_id'], 
                entity=Table.album
        )

@project_structure_bp.route('/get_project_by_id',methods=['GET']) # ocupas todo?
@token_required
def get_project(token_data,original_token):
    project_id = request.args.get('project_id', type=int)

    if not project_id:
        return jsonify({'status': 'error', 'message': Status.NOT_ENTERED.value, 'project_id': project_id})
    cursor = None
    try:
        cursor = mysql.connection.cursor()
        query = """SELECT * FROM project WHERE project_id = %s """
        cursor.execute(query,(project_id,))
        response = cursor.fetchall()
        return ({'status':'success','message':Status.SUCCESSFULLY_CONSULTED.value,'response':response}),200
    except Exception as e:
        return jsonify({'status':'error','message':str(e)}),400
 

@project_structure_bp.route('/get_location_by_id',methods=['GET'])
@token_required
def get_location(token_data,original_token):
    location_id = request.args.get('location_id', type=int)

    if not location_id:
        return jsonify({'status': 'error', 'message': Status.NOT_ENTERED.value, 'location_id':location_id})
    cursor = None
    try:
        cursor = mysql.connection.cursor()
        query = """SELECT * FROM location WHERE location_id = %s """
        cursor.execute(query,(location_id,))
        response = cursor.fetchall()
        return ({'status':'success','message':Status.SUCCESSFULLY_CONSULTED.value,'response':response}),200
    except Exception as e:
        return jsonify({'status':'error','message':str(e)}),400


@project_structure_bp.route('/get_album_by_id',methods=['GET'])
@token_required
def get_album(token_data,original_token):
    album_id = request.args.get('album_id', type=int)

    if not album_id:
        return jsonify({'status': 'error', 'message': Status.NOT_ENTERED.value, 'album_id':album_id})
    cursor = None
    try:
        cursor = mysql.connection.cursor()
        query = """SELECT * FROM album WHERE album_id = %s """
        cursor.execute(query,(album_id,))
        response = cursor.fetchall()
        return ({'status':'success','message':Status.SUCCESSFULLY_CONSULTED.value,'response':response}),200
    except Exception as e:
        return jsonify({'status':'error','message':str(e)}),400