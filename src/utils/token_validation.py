from functools import wraps
from flask import jsonify, current_app, request
import jwt

def valid_token(token):
    print(token)
    if not token:
        return jsonify({ 'message' : 'Token is missing'}), 403
    try:
        data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return jsonify({ 'message' : 'Token has expired '}), 403
    except jwt.InvalidTokenError:
        return jsonify({ 'message' : 'Invalid token'}), 403
    except Exception as e:
        return jsonify({ 'message' : str(e) })
        
    return data

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        validation_result = valid_token(token)

        if isinstance(validation_result, tuple):
                return validation_result
        
        return f(*args, **kwargs, token_data = validation_result, original_token=token)
    return decorated 

