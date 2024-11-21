from flask import Blueprint, jsonify, request
from app.extensions import mysql
from utils.token_validation import token_required
from utils.database_verification import exist_record_in_table
from utils.audit import Table, StatusResponse, Transaccion, register_audit
from utils.message_status import Status

tags_and_categories_bp = Blueprint('tags_categories', __name__, url_prefix='/tag_system')


    
@tags_and_categories_bp.route('/create_category', methods=['POST'])
@token_required
def create_category(token_data, original_token):

    category_name = request.form.get('category_name', type=str)
    status_response = ""
    message_enpoint = ""
    
    if not category_name:
        return jsonify({'status': StatusResponse.ERROR.value, 'message':  Status.NOT_ENTERED.value, 'category_name': category_name }), 400   
    
    cursor = None
    try:
        cursor = mysql.connection.cursor()
        query = """
                    INSERT INTO 
                        category(name)
                    VALUES(%s)
                """
        cursor.execute(query, (category_name,))
        mysql.connection.commit()
        message_enpoint = {'status': StatusResponse.SUCCESS.value, 'message': 'Record was saved correctly', 'category_name' : category_name}
        status_response = StatusResponse.SUCCESS
        return jsonify(message_enpoint), 200
    
    except Exception as e:
        message_enpoint = {'status': StatusResponse.ERROR.value, 'message': str(e) }
        status_response = StatusResponse.ERROR
        return jsonify(message_enpoint), 500
    
    finally:
        if cursor:
            cursor.close()
        register_audit(
                type_=Transaccion.CREATE, 
                request=request.url,
                message= message_enpoint,
                status= status_response,
                user_id= token_data['user_id'], 
                entity=Table.category
        )


@tags_and_categories_bp.route('/show_categories', methods=['GET'])
@token_required
def show_categories(token_data, original_token):

    page = request.args.get('page', default=1, type=int)
    quantity = request.args.get('quantity', default=20, type=int)
    offset = ( page - 1 ) * quantity
    try:
        cursor = mysql.connection.cursor()
        query = """
                    SELECT 
                         category_id, name
                    FROM 
                        category
                    LIMIT %s
                    OFFSET %s
                """
        cursor.execute(query, (quantity, offset))
        response = cursor.fetchall()
        return jsonify({'status': StatusResponse.SUCCESS.value, 'message' : 'Consulted correctly', 'response' : response}), 200
    
    except Exception as e:
        return jsonify({'status': StatusResponse.ERROR.value, 'message' : str(e) }), 500

    finally:
        if cursor:
            cursor.close()


@tags_and_categories_bp.route('/update_category', methods = ['PATCH'])
@token_required
def update_category(token_data, original_token):
    category_id = request.form.get('category_id', type=int)
    category_name = request.form.get('category_name', type=str)
    status_response = ""
    message_enpoint = ""

    if not category_id or not category_name:
        return jsonify({'message' : Status.NOT_ENTERED.value, 'category_id' : category_id, 'category_name' : category_name}), 400
    
    if not exist_record_in_table("category", "name", category_id):
        return jsonify({'status': StatusResponse.ERROR.value, 'message' : Status.RECORD_NOT_FOUND.value}), 404
    
    cursor = None
    try:
        cursor = mysql.connection.cursor()
        query = """
                    UPDATE 
                        category
                    SET 
                        name = %s
                    WHERE 
                        category_id = %s
                """
        cursor.execute(query,(category_name, category_id))
        mysql.connection.commit()
        status_response = StatusResponse.SUCCESS
        message_enpoint = {'status': StatusResponse.SUCCESS.value, 'message' : 'Successfully updated'}
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
                entity=Table.category
        )
    

@tags_and_categories_bp.route('/delete_category', methods = ['DELETE'])
@token_required
def delete_category(token_data, original_token):
    category_id = request.form.get('category_id', type=int)
    table = 'category'
    parameter = 'category_id'
    status_response = ""
    message_enpoint = ""

    if not category_id:
        return jsonify({'message' : Status.NOT_ENTERED.value, 'category_id' : category_id}), 400
    
    if not exist_record_in_table(table, parameter, category_id):
        return jsonify({'status': StatusResponse.ERROR.value, 'message': 'The requested record was not found, please check again.'}), 404
    
    cursor = None
    try:
        cursor = mysql.connection.cursor()
        query = """
                    DELETE FROM
                        category
                    WHERE
                        category_id = %s
                """
        cursor.execute(query, (category_id, ))
        mysql.connection.commit()
        status_response = StatusResponse.SUCCESS
        message_enpoint = {'status': StatusResponse.SUCCESS.value, 'message' : 'Correctly deleted'}
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
                entity=Table.category
        )
        
@tags_and_categories_bp.route('/create_tag', methods=['POST'])
@token_required
def create_tag(token_data, original_token):
    
    tag_name = request.form.get('tag_name', type=str)
    category_id = request.form.get('category_id', type=int)
    status_response = ""
    message_enpoint = ""

    if not tag_name or not category_id:
        return jsonify({'status': StatusResponse.ERROR.value, 'message' : Status.NOT_ENTERED.value, 'tag_name' : tag_name, 'category_id' : category_id }), 400
    
    cursor = None
    try:
        cursor = mysql.connection.cursor()
        query = """INSERT INTO tag(name, category_id)
        VALUES(%s,%s);"""   
        cursor.execute(query,(tag_name, category_id))        
        mysql.connection.commit()
        status_response = StatusResponse.SUCCESS
        message_enpoint = {'status': StatusResponse.SUCCESS.value, 'message': str(Status.SUCCESSFULLY_CREATED), 'tag_name' : tag_name, 'category_id' : category_id}

        return jsonify(message_enpoint), 200
    
    except Exception as e:
        status_response = StatusResponse.ERROR
        message_enpoint = {'status': StatusResponse.ERROR.value, 'message': str(e) }

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
                entity=Table.tag
        )


@tags_and_categories_bp.route('/update_tag', methods=['PATCH'])
@token_required
def update_tag(token_data, original_token):
    
    tag_id = request.form.get('tag_id', type=int)
    tag_name = request.form.get('tag_name', type=str)
    category_id = request.form.get('category_id', type=int)
    status_response = ""
    message_enpoint = ""


    if not tag_name or not category_id or not tag_id:
        return jsonify({'status': StatusResponse.ERROR.value, 'message' : Status.NOT_ENTERED.value, 'tag_id': tag_id ,'tag_name' : tag_name, 'category_id' : category_id }), 400
    
    if not exist_record_in_table("tag", "tag_id", tag_id):
        return jsonify({'status': StatusResponse.ERROR.value, 'message' : Status.RECORD_NOT_FOUND.value}), 404

    cursor = None
    try:
        cursor = mysql.connection.cursor()
        query = """
                    UPDATE 
                        tag
                    SET 
                        name=%s, category_id=%s
                    WHERE 
                        tag_id = %s
                """   
        cursor.execute(query,(tag_name, category_id, tag_id))        
        mysql.connection.commit()
        message_enpoint = {'status': StatusResponse.SUCCESS.value, 'message': Status.SUCCESSFULLY_UPDATED.value, 'tag_name' : tag_name, 'category_id' : category_id}
        status_response = StatusResponse.SUCCESS
        return jsonify(message_enpoint), 200
    
    except Exception as e:
        status_response = StatusResponse.ERROR
        message_enpoint = {'status': StatusResponse.ERROR.value, 'message': str(e) }
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
                    entity=Table.tag
        )
    
@tags_and_categories_bp.route('/show_tags', methods=['GET'])
@token_required
def show_tags(token_data, original_token):

    category_id = request.args.get('category_id', type=int)
    page = request.args.get('page', default=1, type=int)
    quantity = request.args.get('quantity', default=20, type=int)
    offset = ( page - 1 ) * quantity

    if not category_id:
        return jsonify({'status': StatusResponse.ERROR.value, 'message': Status.NOT_ENTERED.value, 'category_id': category_id}),400
    
    cursor = None
    try:
        cursor = mysql.connection.cursor()
        query = """
                    SELECT 
                        tag_id , name, category_id
                    FROM 
                        tag
                    WHERE
                        category_id = %s
                    LIMIT %s
                    OFFSET %s
                """
        cursor.execute(query, (category_id, quantity, offset))
        response = cursor.fetchall()
        return jsonify({'status': StatusResponse.SUCCESS.value, 'message' : 'Consulted correctly', 'response' : response}), 200
    
    except Exception as e:
        return jsonify({'status': StatusResponse.ERROR.value, 'message' : str(e) }), 500

    finally:
        if cursor:
            cursor.close()


@tags_and_categories_bp.route('/show_tags_from_picture', methods=['GET'])
@token_required
def show_tags_from_picture(token_data, original_token):
    picture_id = request.args.get('picture_id', type=str)

    if not picture_id:
            return jsonify({'status': StatusResponse.ERROR.value, 'message': Status.NOT_ENTERED.value, 'picture_id': picture_id}), 400

    cursor = None
    try:
        cursor = mysql.connection.cursor()
        query = """
                    SELECT
                        t.name
                    FROM
                        picture AS p
                    JOIN category AS c
                    ON p.category_id = c.picture_id
                    JOIN tag AS t
                    ON c.category_id = t.category_id
                    WHERE
                        p.picture_id = %s
                """
        cursor.execute(query, (picture_id, ))
        response = cursor.fetchall()
        return jsonify({'status': StatusResponse.SUCCESS.value, 'message': response})
    except Exception as e:
        return jsonify({'status': StatusResponse.ERROR.value, 'message': str(e)}), 500


@tags_and_categories_bp.route('/delete_tag', methods=['DELETE'])
@token_required
def delete_tag(token_data, original_token):
    tag_id = request.form.get('tag_id', type=int)
    table = 'tag'
    parameter = 'tag_id'
    status_response = ""
    message_enpoint = ""

    if not tag_id:
        return jsonify({'status': StatusResponse.ERROR.value, 'message': Status.NOT_ENTERED.value, 'tag_id': tag_id}), 400
    
    if not exist_record_in_table(table, parameter, tag_id):
        return jsonify({'status': StatusResponse.ERROR.value, 'message': 'The requested record was not found, please check again.'}), 404
    
    cursor = None
    try:
        cursor = mysql.connection.cursor()
        query = """
                    DELETE FROM
                        tag
                    WHERE
                        tag_id = %s
                """
        cursor.execute(query, (tag_id, ))
        mysql.connection.commit()
        
        status_response = StatusResponse.SUCCESS
        message_enpoint = {'status': StatusResponse.SUCCESS.value, 'message' : 'Correctly deleted', 'tag_id': tag_id}
        return jsonify(message_enpoint), 200

    except Exception as e:
        status_response = StatusResponse.ERROR
        message_enpoint = {'status': StatusResponse.ERROR.value, 'message': str(e)}

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
                entity=Table.tag
        )

@tags_and_categories_bp.route('/tag_statistics', methods=['GET'])
@token_required
def tag_statistics(token_data, original_token):
    tag_id = request.args.get('tag_id', type=int)
    
    print(tag_id)
    cursor = None
    if not tag_id:
        return jsonify({'status': StatusResponse.ERROR.value, 'message': Status.NOT_ENTERED.value, 'tag_id':tag_id})
    
    try:
        cursor = mysql.connection.cursor()        
        query = """
                    SELECT
                        COUNT(rating_id)
                    FROM
                        rating
                    WHERE
                        tag_id = %s
                """
        cursor.execute(query, (tag_id, ))
        response = cursor.fetchone()
        return jsonify({'status': StatusResponse.SUCCESS.value, 'message': response}), 200
    except Exception as e:
        return jsonify({'status': StatusResponse.ERROR.value, 'message': str(e)})