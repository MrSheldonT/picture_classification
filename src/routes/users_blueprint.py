import jwt
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request, current_app, url_for
from app.extensions import mysql, bcrypt
from src.utils.database_verification import exist_record_in_table
from src.utils.validate_data import valid_email, valid_password, valid_user
from src.utils.token_validation import token_required
from utils.audit import Table, StatusResponse, Transaccion, register_audit
from utils.message_status import Status

users_bp = Blueprint('users', __name__, url_prefix='/users')
default_id = 1
@users_bp.route('/register', methods=['POST'])
def register():
    user_name = request.form.get('user_name', type=str)
    user_email = request.form.get('user_email', type=str)
    user_password = request.form.get('user_password', type=str) 
    user_repeat_password = request.form.get('user_repeat_password', type=str)
    message_endpoint = ""
    status_response = ""

    cursor = None
    if not user_name or not user_password or not user_repeat_password or not user_email:
        return jsonify({'status': StatusResponse.ERROR.value, 'message': Status.NOT_ENTERED.value, 'user_name' : user_name, 'user_email': user_email, 'user_password' : user_password, 'user_repeat_password': user_repeat_password}), 400
    
    if user_repeat_password != user_password:
        return jsonify({'status': StatusResponse.ERROR.value, 'message': 'Passwords are not the same', 'user_password' : user_password, 'user_repeat_password': user_repeat_password }), 400

    if not valid_email(user_email):
        return jsonify({'status': StatusResponse.ERROR.value, 'message': 'The email that you are trying to register is not valid'}), 400
    
    if not valid_user(user_name): 
        return jsonify({'status': StatusResponse.ERROR.value, 'message': 'The username you are trying to register is not valid. It must be alphanumeric and between 3 and 50 characters long.'}), 400
                                                        
    if not valid_password(user_password):
        return jsonify({'status': StatusResponse.ERROR.value, 'message': 'Password must be longer than 5 characters'}), 400

    if exist_record_in_table("user","email", user_email):
        return jsonify({'status': StatusResponse.ERROR.value, 'message': 'The email that you are trying to register already exists'}), 409
    
    if exist_record_in_table("user","name", user_name):
         return jsonify({'status': StatusResponse.ERROR.value, 'message': 'The user that you are trying to register already exists'}), 409
    try:
        user_password = bcrypt.generate_password_hash(user_password).decode('utf-8')
        cursor = mysql.connection.cursor()
        query = """
                    INSERT INTO user(name, password, email)
                    VALUES(%s, %s, %s)
                """
        cursor.execute(query, (user_name, user_password, user_email)) 
        mysql.connection.commit()

        status_response = StatusResponse.SUCCESS
        message_endpoint = {'status': StatusResponse.SUCCESS.value, 'message': 'Account successfully created', 'user_name' : user_name, 'user_email': user_email}
        return jsonify(message_endpoint), 201
    
    except Exception as e:
        status_response = StatusResponse.ERROR
        message_endpoint = {'status': StatusResponse.ERROR.value, 'message': str(e) }
        return jsonify(message_endpoint) ,500
    
    finally:
    
        if cursor:
            cursor.close()
        register_audit(
                type_=Transaccion.CREATE, 
                request=request.url,
                message= message_endpoint,
                status= status_response,
                user_id= default_id, 
                entity=Table.user
            )
        

@users_bp.route('/show_users', methods=['GET'])
@token_required
def show_users(token_data, original_token):

    cursor = None
    message_endpoint = ""
    try:
        page = request.args.get('page', default=1, type=int)
        quantity = request.args.get('quantity', default=50, type=int)
        offset = (page - 1) * quantity 

        cursor = mysql.connection.cursor()
        query = """
                    SELECT 
                        user_id, name, email, confirmed_on
                    FROM 
                        user
                    LIMIT %s
                    OFFSET %s
                """
        cursor.execute(query, (quantity, offset))
        response = cursor.fetchall()      
        message_endpoint = {'status': StatusResponse.SUCCESS.value, 'message' : 'Consulted correctly', 'response' : response}
        return jsonify(message_endpoint), 200
    
    except Exception as e:
        message_endpoint = {'status': StatusResponse.ERROR.value, 'message' : str(e) }
        return jsonify(message_endpoint), 500
    
    finally:
        if cursor:
            cursor.close()

@users_bp.route('/update_status_user', methods=['PATCH'])
@token_required
def update_status_user(token_data, original_token):
    user_id = request.form.get('user_id', type=int)
    user_status = request.form.get('user_status', type=int)
    status_response = ""
    message_endpoint = ""
    if user_id is None and user_status is None:
        return jsonify({'status': StatusResponse.ERROR.value, 'message': Status.NOT_ENTERED.value, 'user_id': user_id, 'user_status': user_status})
    
    if not exist_record_in_table("user","user_id", user_id):
        return jsonify({'status': StatusResponse.ERROR.value, 'message': 'The user that you are trying to modify do not exists'}), 409
    
    if user_id not in(1,2) and token_data['user_id'] not in(1,2): #update the id for administrator
        return jsonify({'status': StatusResponse.ERROR.value, 'message': 'The user that you are trying to modify is administrator'}), 409
    cursor = None
    try:
        cursor = mysql.connection.cursor()
        query = """
                    UPDATE
                        user
                    SET
                        confirmed_on = %s
                    WHERE
                        user_id = %s
                """
        cursor.execute(query, (user_status, user_id))
        mysql.connection.commit()
        message_endpoint = {'status': StatusResponse.SUCCESS.value, 'message': Status.SUCCESSFULLY_UPDATED.value, 'user_id': user_id}
        status_response = StatusResponse.SUCCESS
        return jsonify(message_endpoint), 200
    except Exception as e:
        message_endpoint = {'status': StatusResponse.ERROR.value, 'message' : str(e) }
        status_response = StatusResponse.ERROR
        return jsonify(message_endpoint), 500
    finally:
        if cursor:
            cursor.close()
        register_audit(
                type_= Transaccion.UPDATE, 
                request= request.url,
                message= message_endpoint,
                status= status_response,
                user_id= token_data['user_id'], 
                entity= Table.user
            )

@users_bp.route('/update_user', methods=['PATCH'])
@token_required
def update_user(token_data, original_token):

    user_name = request.form.get('user_name', type=str)
    
    user_email = request.form.get('user_email', type=str)
    status_response = ""
    message_endpoint = ""
    if not user_name or not token_data['user_id']:
        return jsonify({'status': StatusResponse.ERROR.value, 'message' : Status.NOT_ENTERED.value, 'user_id' : token_data['user_id'], 'user_name' : user_name}), 400

    if not valid_user(user_name) or not valid_email(user_email):
        return jsonify({'status': StatusResponse.ERROR.value, 'message': 'The email or the username that you are trying to register is not valid'}), 400

    if exist_record_in_table("user","email", user_email):
         return jsonify({'status': StatusResponse.ERROR.value, 'message': 'The email that you are trying to register already exists'}), 409

    if exist_record_in_table("user","name", user_name):
         return jsonify({'status': StatusResponse.ERROR.value, 'message': 'The user that you are trying to register already exists'}), 409
  
    cursor = None

    try:
        
        cursor = mysql.connection.cursor()
        query = """
                    UPDATE 
                        user
                    SET 
                        name= %s, email = %s
                    WHERE 
                        user_id = %s 
                """

        cursor.execute(query, (user_name, user_email, token_data['user_id']))  
        mysql.connection.commit()
        message_endpoint = {'status': StatusResponse.SUCCESS.value, 'message' : 'Successfully updated', 'user_name': user_name, 'user_email': user_email}
        status_response = StatusResponse.SUCCESS
        return jsonify(message_endpoint), 200
    
    except Exception as e:
        message_endpoint = {'status': StatusResponse.ERROR.value, 'message' : str(e) }
        status_response = StatusResponse.ERROR
        return jsonify(message_endpoint), 500

    finally:
        if cursor:
            cursor.close()
        register_audit(
                type_=Transaccion.UPDATE, 
                request=request.url,
                message= message_endpoint,
                status= status_response,
                user_id= token_data['user_id'], 
                entity=Table.user
            )

@users_bp.route('/update_password', methods=['PATCH'])
@token_required
def update_password(token_data, original_token):
    
    old_password = request.form.get('old_password', type=str)
    new_password = request.form.get('new_password', type=str)

    if not old_password or not new_password:
        return jsonify({'status': StatusResponse.ERROR.value, 'message': Status.NOT_ENTERED.value})
        
    if  not valid_password(new_password):
        return jsonify({'status': StatusResponse.ERROR.value, 'message': "The password is not valid"})
    message_enpoint = ""
    status_response = ""
    cursor = None
    try:
        cursor = mysql.connection.cursor()
        query = """
                    SELECT
                        password
                    FROM
                        user
                    WHERE
                        user_id = %s
                """
        cursor.execute(query, (token_data['user_id'],))
        response = cursor.fetchone()[0]
        if response and bcrypt.check_password_hash(response, old_password):
            new_password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
            print(new_password_hash)
            query = """
                        UPDATE
                            user
                        SET
                            password = %s
                        WHERE
                            user_id = %s
                    """
            cursor.execute(query, (new_password_hash, token_data['user_id']))
            mysql.connection.commit()
        message_enpoint = {'status': StatusResponse.ERROR.value, 'message': Status.SUCCESSFULLY_UPDATED }
        status_response = StatusResponse.ERROR
    except Exception as e:
        message_endpoint = {'status': StatusResponse.ERROR.value, 'message': str(e)}
        status_response = StatusResponse.ERROR
        return jsonify(message_endpoint), 500
    finally:
        1
 
@users_bp.route('/login', methods = ['POST'])
def login_user():
    
    user_name = request.form.get('user_name', type=str)
    user_password = request.form.get('user_password', type=str)
    status_response = StatusResponse.ERROR
    message_endpoint = ""
    user = ""

    if not user_name or not user_password:
        return jsonify({'status': StatusResponse.ERROR.value, 'message': Status.NOT_ENTERED.value, 'user_name': user_name, 'user_password' : user_password}), 400

    cursor = None
    try:       
        cursor = mysql.connection.cursor()
        query = """
                    SELECT 
                        user_id, name, password, confirmed_on
                    FROM 
                        user
                    WHERE 
                        (name = %s OR email = %s)
                    ;
                """
        cursor.execute(query, (user_name, user_name))
        user = cursor.fetchone()
        if user is None:
            message_endpoint = {'status': StatusResponse.ERROR.value, 'message': 'The account does not exist'}
            status_response = StatusResponse.ERROR    
            return jsonify(message_endpoint), 401
        
        if user[3] == 0:
            return jsonify({'status': StatusResponse.ERROR.value, 'message': 'Account denied, please contact administration for permission'}), 403
                                                                            
        if user and bcrypt.check_password_hash(user[2], user_password):            
            token = jwt.encode({
                'user_id': user[0],
                'exp' : datetime.now() + timedelta(hours=24)
            }, current_app.config['SECRET_KEY'], algorithm='HS256')
            message_endpoint = {'status': StatusResponse.SUCCESS.value, 'message' : 'Successful login', 'token' : token}
            status_response = StatusResponse.SUCCESS.value

            return jsonify(message_endpoint), 200
        
        
        message_endpoint = {'status': StatusResponse.ERROR.value, 'message': 'Incorrect username or password'}
        status_response = StatusResponse.ERROR.value
        return jsonify(message_endpoint), 401
    
    except Exception as e:
        message_endpoint = {'status': StatusResponse.ERROR.value, 'message': str(e)}
        status_response = StatusResponse.ERROR.value
        return jsonify(message_endpoint), 500
    
    finally:
        if cursor:
            cursor.close()
        if user is not None:
            register_audit(
                    type_=Transaccion.OTHERS.value, 
                    request=request.url,
                    message= message_endpoint,
                    status=status_response, 
                    user_id=user[0], 
                    entity=Table.user
                )