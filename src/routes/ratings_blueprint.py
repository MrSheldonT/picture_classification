from flask import Blueprint, jsonify, request
from utils.token_validation import token_required
from datetime import datetime
from app.extensions import mysql
from utils.database_verification import exist_record_in_table
from utils.audit import Table, StatusResponse, Transaccion, register_audit
from utils.message_status import Status

ratings_bp = Blueprint('ratings', __name__, url_prefix='/ratings')

@ratings_bp.route('/create_rating', methods=['POST'])
@token_required
def create_rating(token_data, original_token):
    picture_id = request.form.get('picture_id', type=str)
    tag_id = request.form.get('tag_id', type=int)
    rating_score = request.form.get('rating_score', type=float)
    rating_date = request.form.get('rating_date', type=str, default=datetime.today().strftime('%Y-%m-%d') )
    status_response = ""
    message_enpoint = ""
    if not picture_id or not token_data['user_id'] or not rating_date or not tag_id:
        return jsonify({'status': StatusResponse.ERROR.value, 'message' : Status.NOT_ENTERED.value, 'picture_id' : picture_id, 'user_id' : token_data['user_id'], 'rating_score' : rating_score, 'date' : rating_date, 'tag_id': tag_id })
    
    if rating_score < 0 and rating_score > 3:
        return jsonify({'status': StatusResponse.ERROR.value, 'message': 'value for score is invalid'})

    cursor = None
    try:
        cursor = mysql.connection.cursor()
        query = """
            SELECT 
                user_id
            FROM
                rating
            WHERE
                picture_id=%s and tag_id=%s and user_id=%s
        """
        cursor.execute(query,(picture_id, tag_id, token_data['user_id'] ))
        response = cursor.fetchone()
        
        if response is not None:
            return jsonify({'status': StatusResponse.ERROR.value, 'message': 'The rating already exists'})
        
        query = """
                    INSERT INTO 
                        rating(picture_id, user_id, score, date, tag_id)
                    VALUES(%s, %s, %s, %s, %s)
                """
        
        cursor.execute(query,(picture_id, token_data['user_id'], rating_score, rating_date, tag_id))
        mysql.connection.commit()
        new_rating_id = cursor.lastrowid
 
        status_response = StatusResponse.SUCCESS.value
        message_enpoint = {'status': StatusResponse.SUCCESS.value, 'message' : 'The rating was recorded correctly', 'rating_id': new_rating_id, 'picture_id' : picture_id, 'user_id' : token_data['user_id'], 'score' : rating_score, 'date' : rating_date, 'tag_id': tag_id}

        return jsonify(message_enpoint), 201
    
    except Exception as e:
        status_response = StatusResponse.ERROR.value
        message_enpoint = {'status': StatusResponse.ERROR.value, 'message': str(e) }

        return jsonify(message_enpoint), 500
    
    finally:
        if cursor:
            cursor.close()
        register_audit(
                type_=Transaccion.CREATE.value, 
                request=request.url,
                message=message_enpoint,
                status=status_response,
                user_id=token_data['user_id'], 
                entity=Table.rating
        )

    
@ratings_bp.route('/show_ratings_from_picture', methods=['GET'])
@token_required
def show_ratings_from_picture(token_data, original_token):

    page = request.args.get('page', default=1, type=int)
    quantity = request.args.get('quantity', default=50, type=int)
    picture_id = request.args.get('picture_id', type=str)
    offset = (page - 1) * quantity 

    if not picture_id:
        return jsonify({'status' : StatusResponse.ERROR.value , 'message' : str(Status.NOT_ENTERED), 'picture_id' : picture_id }), 400
    
    cursor = None
    try:
        cursor = mysql.connection.cursor()
        query = """
                    SELECT  
                        rating.user_id, rating.picture_id, rating.score, rating.date,rating.tag_id,rating.rating_id,tag.name,user.name,category.category_id 
                    FROM 
                        rating
                    JOIN tag ON tag.tag_id = rating.tag_id
                    JOIN user ON user.user_id = rating.user_id
                    JOIN category ON tag.category_id = category.category_id
                    WHERE 
                        picture_id = %s
                    LIMIT %s
                    OFFSET %s
                """
        cursor.execute(query, (picture_id, quantity, offset))
        response = cursor.fetchall()
        return jsonify({'status': StatusResponse.SUCCESS.value,  'message' : 'Consulted correctly', 'response' : response}), 200
    
    except Exception as e:
        return jsonify({'status': StatusResponse.ERROR.value,  'message' : str(e) }), 500
    finally:
        if cursor:
            cursor.close()
    
@ratings_bp.route('/show_ratings_from_user', methods=['GET'])
@token_required
def show_rating_from_user(token_data, original_token):
    
    page = request.args.get('page', default=1, type=int)
    quantity = request.args.get('quantity', default=50, type=int)
    picture_id = request.args.get('picture_id',type=str)
    user_id = request.args.get('user_id', type=int)
    category_id = request.args.get('category_id',type=int)
    offset = (page - 1) * quantity 
    
    if not all([user_id,category_id,picture_id]):
        return jsonify({'status': StatusResponse.ERROR.value, 'message': str(Status.NOT_ENTERED), 'user_id': user_id,'category_id':category_id,'picture_id':picture_id})
    
    cursor = None
    try:
        cursor = mysql.connection.cursor()
        query = """
                    SELECT
                        rating.user_id, rating.picture_id, rating.score, rating.date, rating.tag_id ,rating.rating_id,tag.name,category.category_id
                    FROM 
                        rating
                    JOIN
                        tag ON tag.tag_id = rating.tag_id
                    JOIN
                        category ON tag.category_id = category.category_id
                    WHERE
                        rating.user_id = %s and rating.picture_id = %s and category.category_id = %s
                    LIMIT %s
                    OFFSET %s
                """
        cursor.execute(query, (user_id,picture_id,category_id, quantity, offset))
        response = cursor.fetchall()
        return jsonify({'status': StatusResponse.SUCCESS.value, 'message': 'Consulted correctly', 'response': response}), 200
    
    except Exception as e:
        return jsonify({'status': StatusResponse.ERROR.value, 'message': str(e)}), 500
    
    finally:        
        if cursor:
            cursor.close()
    
@ratings_bp.route('/update_rating', methods=['PATCH'])
@token_required
def update_rating(token_data, original_token):
    picture_id = request.form.get('picture_id', type=str)
    rating_score = request.form.get('rating_score', type=float)
    rating_date = request.form.get('rating_date', type=str, default=datetime.today().strftime('%Y-%m-%d') )
    tag_id = request.form.get('tag_id', type=int)
    status_response = ""
    message_enpoint = ""

    if not picture_id or not rating_date or not tag_id:
        return jsonify({'status': StatusResponse.ERROR.value, 'message' : Status.NOT_ENTERED.value, 'picture_id' : picture_id, 'user_id' : token_data['user_id'], 'score' : rating_score, 'tag_id':tag_id,'date' : rating_date }), 400
    
    if rating_score < 0 and rating_score > 3:
        return jsonify({'status': StatusResponse.ERROR.value, 'message': 'value for score is invalid'})

    cursor = None
    try:
        cursor = mysql.connection.cursor()
        query = """
                    UPDATE 
                        rating
                    SET 
                        score=%s, date=%s
                    WHERE 
                        picture_id=%s and user_id=%s  and tag_id=%s
                """
        cursor.execute(query, (rating_score, rating_date, picture_id, token_data['user_id'], tag_id))    
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
                entity=Table.rating
        )

@ratings_bp.route('/delete_rating', methods = ['DELETE'])
@token_required
def delete_rating(token_data, original_token):
    rating_id = request.form.get('rating_id', type=int)
    table = 'rating'
    parameter = 'rating_id'

    if not rating_id:
         return jsonify({'status': StatusResponse.ERROR, 'message': Status.NOT_ENTERED.value, 'rating_id': rating_id}), 400

    if not exist_record_in_table(table, parameter, rating_id):
        return jsonify({'status': StatusResponse.ERROR.value, 'message': 'The requested record was not found, please check again.'}), 404

    cursor = None
    try:
        cursor = mysql.connection.cursor()
        query = """
                    DELETE FROM
                        rating
                    WHERE 
                        rating_id = %s
                """
        cursor.execute(query, (rating_id, ))
        mysql.connection.commit()
        return jsonify({'status': StatusResponse.SUCCESS.value, 'message' : 'Correctly deleted'}), 200
    
    except Exception as e:
        return jsonify({'status': StatusResponse.ERROR.value, 'message': str(e)}), 500

    finally:
        if cursor:
            cursor.close()

@ratings_bp.route('/rating_average', methods=['GET'])
@token_required
def rating_average(token_data, original_token):
    picture_id = request.args.get('picture_id', type=str)
    tag_id = request.args.get('tag_id', type=str)

    if not tag_id or not picture_id:
        return jsonify({'status': StatusResponse.ERROR.value, 'message': Status.NOT_ENTERED.value, 'id_picture': picture_id, 'tag_id': tag_id})

    try:
        cursor = mysql.connection.cursor()
        query = """
                    SELECT
                        AVG(score)
                    FROM
                        rating
                    WHERE
                        picture_id = %s AND tag_id = %s
                    ;
                """
        cursor.execute(query, (picture_id, ))
        rating_average = cursor.fetchone()
        return jsonify({'status': StatusResponse.ERROR.value, 'message': Status.SUCCESSFULLY_CONSULTED.value,'rating_average': rating_average})
    except Exception as e:
        return jsonify({'status': StatusResponse.ERROR.value, 'message': str(e)})