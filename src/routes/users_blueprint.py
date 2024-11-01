import jwt
from datetime import datetime, timedelta
from flask_mail import Message
from flask import Blueprint, jsonify, request, current_app, url_for
from app.extensions import mysql, bcrypt, mail
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
    message_enpoint = ""
    status_response = ""

    cursor = None
    if not user_name or not user_password or not user_repeat_password or not user_email:
        return jsonify({'status': 'error', 'message': Status.NOT_ENTERED.value, 'user_name' : user_name, 'user_email': user_email, 'user_password' : user_password, 'user_repeat_password': user_repeat_password}), 400
    
    if user_repeat_password != user_password:
        return jsonify({'status': 'error', 'message': 'Passwords are not the same', 'user_password' : user_password, 'user_repeat_password': user_repeat_password }), 400

    if not valid_email(user_email):
        return jsonify({'status': 'error', 'message': 'The email that you are trying to register is not valid'}), 400
    
    if not valid_user(user_name): 
        return jsonify({'status': 'error', 'message': 'The username you are trying to register is not valid. It must be alphanumeric and between 3 and 50 characters long.'}), 400
                                                        
    if not valid_password(user_password):
        return jsonify({'status': 'error', 'message': 'Password must be longer than 5 characters'}), 400

    if exist_record_in_table("user","email", user_email):
         return jsonify({'status': 'error', 'message': 'The email that you are trying to register already exists'}), 409
    
    if exist_record_in_table("user","name", user_name):
         return jsonify({'status': 'error', 'message': 'The user that you are trying to register already exists'}), 409
    try:
        user_password = bcrypt.generate_password_hash(user_password).decode('utf-8')
        cursor = mysql.connection.cursor()
        query = """
                    INSERT INTO user(name, password, email)
                    VALUES(%s, %s, %s)
                """
        cursor.execute(query, (user_name, user_password, user_email)) 
        mysql.connection.commit()

        #send_verification_email(user_email=user_email) the token has expired
        status_response = StatusResponse.SUCCESS
        message_enpoint = {'status': 'success', 'message': 'Account successfully created', 'user_name' : user_name, 'user_email': user_email}
        return jsonify(message_enpoint), 201
    
    except Exception as e:
        status_response = StatusResponse.ERROR
        message_enpoint = {'status': 'error', 'message': str(e) }
        return jsonify(message_enpoint) ,500
    
    finally:
    
        if cursor:
            cursor.close()
        register_audit(
                type_=Transaccion.CREATE, 
                request=request.url,
                message= message_enpoint,
                status= status_response,
                user_id= default_id, 
                entity=Table.user
            )
        

@users_bp.route('/show_users', methods=['GET'])
@token_required
def show_users(token_data, original_token):

    cursor = None
    message_enpoint = ""
    try:
        page = request.args.get('page', default=1, type=int)
        quantity = request.args.get('quantity', default=50, type=int)
        offset = (page - 1) * quantity 

        cursor = mysql.connection.cursor()
        query = """
                    SELECT 
                        user_id, name, email
                    FROM 
                        user
                    LIMIT %s
                    OFFSET %s
                """
        cursor.execute(query, (quantity, offset))
        response = cursor.fetchall()      
        message_enpoint = {'status': 'success', 'message' : 'Consulted correctly', 'response' : response}
        return jsonify(message_enpoint), 200
    
    except Exception as e:
        message_enpoint = {'status': 'error', 'message' : str(e) }
        return jsonify(message_enpoint), 500
    
    finally:
        if cursor:
            cursor.close()

@users_bp.route('/update_user', methods=['PATCH'])
@token_required
def update_user(token_data, original_token):

    user_name = request.form.get('user_name', type=str)
    user_password = request.form.get('user_password', type=str) 
    user_email = request.form.get('user_email', type=str)
    status_response = ""
    message_enpoint = ""
    if not user_name or not user_password or not token_data['user_id']:
        return jsonify({'status': 'error', 'message' : Status.NOT_ENTERED.value, 'user_id' : token_data['user_id'], 'user_name' : user_name, 'user_password' : user_password}), 400

    if not valid_user(user_name) or not valid_email(user_email) or not valid_password(user_password):
        return jsonify({'status': 'error', 'message': 'The email or the username that you are trying to register is not valid'}), 400

    if exist_record_in_table("user","email", user_email):
         return jsonify({'status': 'error', 'message': 'The email that you are trying to register already exists'}), 409
    # proceso sobre validación de correo y cambio en caso de existir    
    if exist_record_in_table("user","name", user_name):
         return jsonify({'status': 'error', 'message': 'The user that you are trying to register already exists'}), 409
  
    cursor = None

    try:
        user_password = bcrypt.generate_password_hash(user_password).decode('utf-8')
        cursor = mysql.connection.cursor()
        query = """
                    UPDATE 
                        user
                    SET 
                        name= %s, password= %s, email = %s
                    WHERE 
                        user_id = %s 
                """

        cursor.execute(query, (user_name, user_password, user_email, token_data['user_id']))  
        mysql.connection.commit()
        message_enpoint = {'status': 'success', 'message' : 'Successfully updated', 'user_name': user_name, 'user_email': user_email}
        status_response = StatusResponse.SUCCESS
        return jsonify(message_enpoint), 200
    
    except Exception as e:
        message_enpoint = {'status': 'error', 'message' : str(e) }
        status_response = StatusResponse.ERROR
        return jsonify(message_enpoint), 500

    finally:
        if cursor:
            cursor.close()
        register_audit(
                type_=Transaccion.UPDATE, 
                request=request.url,
                message= message_enpoint,
                status= status_response,
                user_id= token_data['user_id'], 
                entity=Table.user
            )

@users_bp.route('/confirm_email<token>', methods=['GET']) ## fix
def confirm_email(token):
    try:
        data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        user_email = data['user_email']

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT confirmed_on FROM user WHERE email = %s", (user_email,))
        user = cursor.fetchone()

        if not user:
            return jsonify({'status': 'error', 'message': 'Invalid user'}), 404

        if user[0] == 'null': # marrafufada  
            return jsonify({'status': 'info', 'message': 'Account already confirmed'}), 200

        cursor.execute("UPDATE user SET confirmed_on = null, confirmed_on = %s WHERE email = %s", (datetime.now(), user_email))
        mysql.connection.commit()

        return jsonify({'status': 'success', 'message': 'Account successfully confirmed'}), 200

    except jwt.ExpiredSignatureError:
        return jsonify({'status': 'error', 'message': 'The confirmation link has expired'}), 400
    except jwt.InvalidTokenError:
        return jsonify({'status': 'error', 'message': 'Invalid token'}), 400
    

@users_bp.route('/login', methods = ['POST'])
def login_user():
    
    user_name = request.form.get('user_name', type=str)
    user_email = request.form.get('user_email', type=str)
    user_password = request.form.get('user_password', type=str)
    status_response = ""
    message_enpoint = ""
    user = ""


    if (not user_name and not user_email) or not user_password:
        return jsonify({'status': 'error', 'message': Status.NOT_ENTERED.value, 'user_name': user_name,'user_email': user_email, 'user_password' : user_password}), 400

    cursor = None
    try:       
        cursor = mysql.connection.cursor()
        query = """
                    SELECT 
                        user_id, name, password
                    FROM 
                        user
                    WHERE 
                        name = %s OR email = %s
                """
        cursor.execute(query, (user_name, user_email))
        user = cursor.fetchone()

        if user and bcrypt.check_password_hash(user[2], user_password):
            print("YAA")
            token = jwt.encode({
                'user_id': user[0],
                'exp' : datetime.now() + timedelta(hours=24)
            }, current_app.config['SECRET_KEY'], algorithm='HS256')
            message_enpoint = {'status': 'success', 'message' : 'Successful login', 'token' : token}
            print("YAA")
            status_response = StatusResponse.SUCCESS
            print("YAA")
            return jsonify(message_enpoint), 200
        message_enpoint = {'status': 'error', 'message': 'Incorrect username or password'}
        status_response = StatusResponse.ERROR
        return jsonify(message_enpoint), 401
    
    except Exception as e:
        message_enpoint = {'status': 'error', 'message': str(e)}
        status_response = StatusResponse.ERROR
        return jsonify(message_enpoint), 500
    
    finally:
        if cursor:
            cursor.close()
        register_audit(
                type_=Transaccion.OTHERS, 
                request=request.url,
                message= message_enpoint,
                status=status_response, 
                user_id=user[0], 
                entity=Table.user
            )

def send_verification_email(user_email):
    try:
        token = jwt.encode({
            'user_email': user_email,
            'exp': datetime.now()  + timedelta(hours=1)  
        }, current_app.config['SECRET_KEY'], algorithm='HS256')

        confirm_url = url_for('miscellaneous.confirm_email', token=token, _external=True)

        subject = 'Confirma tu cuenta'
        html = f'''
        <p>Gracias por registrarte. Por favor, confirma tu cuenta haciendo clic en el enlace:</p>
        <p><a href="{confirm_url}">Confirmar mi cuenta</a></p>
        '''
        msg = Message(subject, sender=current_app.config['MAIL_USERNAME'], recipients=[user_email], html=html)
        mail.send(msg)
    except Exception as e:
        print(str(e))