from flask import Blueprint, jsonify, request
from app.extensions import mysql
from utils.audit import Table, StatusResponse, Transaccion, register_audit
from utils.message_status import Status
from utils.token_validation import token_required


permissions_bp = Blueprint('permissions', __name__, url_prefix='/permissions')

@permissions_bp.route('/user_allowed', methods = ['POST'])
@token_required
def allow_user(token_data, original_token):
    user_id_allowed = request.form.get('user_id_allowed', type=str)
    cursor = None
    status_response = ''
    message_enpoint = ''

    if not user_id_allowed:
        return jsonify({'status': Status.NOT_ENTERED.value, 'user_id_allowed': user_id_allowed})

    try:
        cursor = mysql.connection.cursor()
        query = '''
                    UPDATE
                        user
                    SET
                        confirmed_on = 1
                    WHERE
                        user_id = %s AND user_id != 1
                    ;
                '''
        cursor.execute(query, (user_id_allowed, ))
        mysql.connection.commit()
        message_enpoint = { 'status': StatusResponse.SUCCESS.value, 'message': 'user {user_id_allowed} updated'}
        status_response = StatusResponse.SUCCESS
        return jsonify(message_enpoint)
    except Exception as e:
        message_enpoint = {'status': StatusResponse.ERROR.value, 'message': str(e) }
        status_response = StatusResponse.ERROR
        return jsonify(message_enpoint)
    finally:
        if cursor:
            cursor.close()
        register_audit(
                type_=Transaccion.UPDATE, 
                request=request.url,
                message=message_enpoint,
                status=status_response,
                user_id=token_data['user_id'], 
                entity=Table.user
        )

@permissions_bp.route('/user_denied', methods = ['POST'])
@token_required
def allow_user(token_data, original_token):
    user_id_denied = request.form.get('user_id_denied', type=str)
    cursor = mysql.connection.cursor()
    if not user_id_denied:
        return jsonify({'status': Status.NOT_ENTERED.value, 'user_id_denied': user_id_denied})
    try:
        query = '''
                    UPDATE
                        user
                    SET
                        confirmed_on = 0
                    WHERE
                        user_id = %s AND user_id != 1
                    ;
                '''
        cursor.execute(query, (user_id_denied, ))
        mysql.connection.commit()
        message_enpoint = { 'status': StatusResponse.SUCCESS.value, 'message': 'user {user_id_allowed} updated'}
        status_response = StatusResponse.SUCCESS
    except Exception as e:
        message_enpoint = {'status': StatusResponse.ERROR.value, 'message': str(e) }
        status_response = StatusResponse.ERROR
        return jsonify(message_enpoint)
    finally:
        if cursor:
            cursor.close()
        register_audit(
                type_=Transaccion.UPDATE, 
                request=request.url,
                message=message_enpoint,
                status=status_response,
                user_id=token_data['user_id'], 
                entity=Table.user
        )