from flask import Blueprint, jsonify, request, current_app, send_from_directory
from utils.token_validation import token_required
from app.extensions import mysql
from utils.files import allowed_file, picture_to_hash, save_picture, delete_picture_file, url_for_picture
from utils.database_verification import exist_record_in_table
from utils.audit import Table, StatusResponse, Transaccion, register_audit
from utils.message_status import Status
import os

pictures_bp = Blueprint('pictures', __name__, url_prefix='/pictures')

@pictures_bp.route('/upload_picture', methods=['POST'])
@token_required
def upload_picture(token_data, original_token):
    message_enpoint = ""
    status_response = None
    if 'file' not in request.files:
        return 'No file', 400
    
    file = request.files['file']
    
    if file.filename == '':
        return 'No file selected', 400
    
    album_id = request.form.get('album_id', type=int)
    category_id = request.form.get('category_id', type=int, default=1)
    table = "picture"
    parameter = "picture_id"
    
    if not album_id or not category_id:
        return jsonify({'status': 'error', 'message' : Status.NOT_ENTERED.value, 'album_id' : album_id, 'category_id': category_id }), 400
    
    if file and allowed_file(file.filename):
        file_content = file.read()
        picture_id = picture_to_hash(file_content)
        file.seek(0)

        if exist_record_in_table(table, parameter,picture_id):
            return jsonify({'status' : 'error', 'message' : 'Image alredy exists'}), 409

        cursor = mysql.connection.cursor()
        upload_folder = current_app.config['UPLOAD_FOLDER']    
        
        try:   
            
            filepath =  save_picture(file, picture_id, upload_folder)
            query = """
                        INSERT INTO 
                            picture (picture_id, path, album_id, category_id)
                        VALUES (%s, %s, %s, %s)
                    """
            
            cursor.execute(query, (picture_id, filepath, album_id, category_id))
            mysql.connection.commit()
            status_response = StatusResponse.SUCCESS
            message_enpoint = {'status': 'success', 'message': 'Record was saved correctly', 'picture_id' : picture_id, 'filepath' : filepath, 'album_id': album_id, 'category_id': category_id}
            return jsonify(message_enpoint), 200
        
        except Exception as e:
            delete_picture_file(file, picture_id, upload_folder)
            status_response = StatusResponse.ERROR
            message_enpoint = {'status': 'error', 'message': str(e) }
            return jsonify(message_enpoint), 400 

        finally:
            if cursor:
                cursor.close()

            register_audit(
                type_=Transaccion.CREATE, 
                request=request.url,
                message= message_enpoint,
                status= status_response,
                user_id=token_data['user_id'], 
                entity=Table.picture
            )
    else:
        return jsonify({'status': 'error', 'message':'File type not allowed' , 'file' : file.filename }), 400

@pictures_bp.route('/uploads/<filename>')
def serve_image(filename):
    upload_folder = current_app.config['UPLOAD_FOLDER']
    return send_from_directory(upload_folder, filename)

@pictures_bp.route('/picture', methods=['GET'])
@token_required
def render_picture(token_data, original_token):

    picture_id = request.args.get('picture_id', type=str)
    
    if not picture_id:
        return jsonify({'status': 'error', 'message': 'No image entered'}), 400

    cursor = None
    try:
        cursor = mysql.connection.cursor()
        query = """
                    SELECT 
                        path, picture_id, date
                    FROM
                        picture
                    WHERE
                        picture_id = %s
                """
        cursor.execute(query, (picture_id,))
        picture = cursor.fetchone()
        
        if picture:
            #path, id, date
            url_picture = url_for_picture(picture[0]), picture[1], picture[2]
            print(url_picture)
            if url_picture:
                return jsonify({'status': 'success', 'picture_url': url_picture}), 200
            else:
                return jsonify({'status': 'error', 'message': 'File not found on the server'}), 404
        else:
            return jsonify({'status': 'error', 'message': 'Image with the provided ID was not found'}), 404

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
    finally:
        if cursor:
            cursor.close()


@pictures_bp.route('/show_all_pictures', methods=['GET'])
@token_required
def show_all_pictures(token_data, original_token):

    page = request.args.get('page', default=1, type=int)
    quantity = request.args.get('quantity', default=20, type=int)
    offset = ( page - 1 ) * quantity
        

    cursor = None
    try:
        cursor = mysql.connection.cursor()
        query = """
                    SELECT 
                        path, picture_id, date
                    FROM 
                        picture
                    LIMIT %s
                    OFFSET %s
                """
        
        cursor.execute(query, (quantity, offset))
        all_pictures = cursor.fetchall()
        url_all_pictures = []
        for picture in all_pictures:
            url_picture = url_for_picture(picture[0]), picture[1], picture[2]
            
            if url_picture:
                url_all_pictures.append(url_picture)
            else:
                print("No valido.")
        if len(url_all_pictures):
            return jsonify({'status': 'success', 'message' : Status.SUCCESSFULLY_CONSULTED.value, 'response' : url_all_pictures}), 200
        else:
            return jsonify({'status': 'success', 'message' : 'Consulted correctly, but there are no images', 'response' : url_all_pictures}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message' : str(e) }), 500

    finally:
        if cursor:
            cursor.close()


@pictures_bp.route('/show_picture_from_album',methods=['GET'])
@token_required
def show_picture_from_album(token_data, original_token):
    
    album_id = request.args.get('album_id', default=1, type=int)
    page = request.args.get('page', default=1, type=int)
    quantity = request.args.get('quantity', default=20, type=int)
    offset = ( page - 1 ) * quantity
    
    if not album_id:
        return jsonify({'status': 'error', 'message': Status.NOT_ENTERED.value, 'album_id': album_id})

    cursor = None
    try:    
        cursor = mysql.connection.cursor()
        query = """
                    SELECT 
                        path, picture_id, date
                    FROM 
                        picture 
                    WHERE 
                        album_id= %s
                    LIMIT %s 
                    OFFSET %s
                """
        
        cursor.execute(query,(album_id,quantity, offset))
        all_pictures = cursor.fetchall()
        url_all_pictures = []
        for picture in all_pictures:
            url_picture = url_for_picture(picture[0]), picture[1], picture[2]
            
            if url_picture:
                url_all_pictures.append(url_picture)
            else:
                print("No valido.")
        if len(url_all_pictures):
            return jsonify({'status': 'success', 'message' : Status.SUCCESSFULLY_CONSULTED.value, 'response' : url_all_pictures}), 200
        else:
            return jsonify({'status': 'success', 'message' : 'Consulted correctly, but there are no images', 'response' : url_all_pictures}), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'message' : str(e) }), 500

    finally:
        if cursor:
            cursor.close()

@pictures_bp.route('/show_picture_from_album_progress',methods=['GET'])
@token_required
def show_picture_from_album_progress(token_data, original_token):
    
    album_id = request.args.get('album_id', default=1, type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    max_pictures = request.args.get('max_pictures', default=10, type=int)
    page = request.args.get('page', default=1, type=int)
    offset = ( page - 1 ) * max_pictures
    
    if not album_id:
        return jsonify({'status': 'error', 'message': Status.NOT_ENTERED.value, 'album_id': album_id})

    cursor = None
    try:    
        cursor = mysql.connection.cursor()
        query = """
                    SELECT 
                        path, picture_id, date
                    FROM 
                        picture 
                    WHERE 
                        album_id= %s
                """
        
        params = [album_id]
        
        if start_date and end_date:
            query +=  " AND date BETWEEN %s AND %s"
            params.extend([start_date, end_date]) 

        query += " ORDER BY date ASC LIMIT %s OFFSET %s"
        params.extend([max_pictures, offset]) 

        cursor.execute(query,tuple(params))
        pictures_by_date = {}
        all_pictures = cursor.fetchall()
    
        for picture in all_pictures:
            path, picture_id, date = picture
            year_month = date.strftime("%Y-%m")
            if year_month not in pictures_by_date:
                pictures_by_date[year_month] = []
            pictures_by_date[year_month].append({
                "url": url_for_picture(path),
                "picture_id": picture_id,
                "date": date
            })
        if pictures_by_date:
            return jsonify({'status': 'success', 'message': 'Pictures retrieved successfully', 'response': pictures_by_date}), 200
        else:
            return jsonify({'status': 'success', 'message': 'No pictures found', 'response': pictures_by_date}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message' : str(e) }), 500

    finally:
        if cursor:
            cursor.close()

@pictures_bp.route('/show_picture_from_location', methods=['GET']) 
@token_required
def show_picture_from_location(token_data, original_token):

    location_id = request.args.get('location_id' , type=int)
    page = request.args.get('page', default=1, type=int)
    quantity = request.args.get('quantity', default=20, type=int)
    offset = ( page - 1 ) * quantity
    
    if not location_id:
        return jsonify({'status': 'error', 'message': Status.NOT_ENTERED.value, 'location_id': location_id})
    try:
        cursor = mysql.connection.cursor()
        query = """
                    SELECT 
                        path, picture_id, pic.date
                    FROM 
                        album AS al
                        JOIN picture AS pic
                        ON al.album_id = pic.album_id 
                    WHERE 
                        al.location_id = %s  
                    LIMIT %s
                    OFFSET %s
                """
        cursor.execute(query,(location_id,quantity, offset))
        all_pictures = cursor.fetchall()
        url_all_pictures = []
        for picture in all_pictures:
            url_picture = url_for_picture(picture[0]), picture[1], picture[2]
            
            if url_picture:
                url_all_pictures.append(url_picture)
            else:
                print("No valido.")
        if len(url_all_pictures):
            return jsonify({'status': 'success', 'message' : Status.SUCCESSFULLY_CONSULTED.value, 'response' : url_all_pictures}), 200
        else:
            return jsonify({'status': 'success', 'message' : 'Consulted correctly, but there are no images', 'response' : url_all_pictures}), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'message' : str(e) }), 500
    
    finally:
        if cursor:
            cursor.close()
    
@pictures_bp.route('/show_picture_from_project', methods = ['GET'])
@token_required
def show_picture_from_project(token_data, original_token):

    project_id = request.args.get('project_id', type=int)
    page = request.args.get('page', default=1, type=int)
    quantity = request.args.get('quantity', default=20, type=int)
    offset = ( page - 1 ) * quantity
    
    if not project_id:
        return jsonify({'status': 'error', 'message': 'Parameters not entered', 'project_id': project_id})

    cursor = None
    try:
        quantity = int(quantity)
        cursor = mysql.connection.cursor()
        query = """
                    SELECT 
                        path, picture_id, pic.date
                    FROM 
                        project
                        JOIN location
                        ON location.project_id = project.project_id
                        JOIN album as alb
                        ON alb.location_id = location.location_id
                        JOIN picture AS pic
                        ON pic.album_id = alb.album_id
                    WHERE 
                        project.project_id = %s
                    LIMIT %s
                    OFFSET %s
                """
        cursor.execute(query,(project_id,quantity, offset ))

        all_pictures = cursor.fetchall()
        url_all_pictures = []
        for picture in all_pictures:
            url_picture = url_for_picture(picture[0]), picture[1], picture[2]
            
            if url_picture:
                url_all_pictures.append(url_picture)
            else:
                print("No valido.")
        if len(url_all_pictures):
            return jsonify({'status': 'success', 'message' : Status.SUCCESSFULLY_CONSULTED.value, 'response' : url_all_pictures}), 200
        else:
            return jsonify({'status': 'success', 'message' : 'Consulted correctly, but there are no images', 'response' : url_all_pictures}), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'message' : str(e)}), 500
    
    finally:
        if cursor:
            cursor.close()
    


@pictures_bp.route('/delete_picture', methods = ['DELETE'])
@token_required
def delete_picture(token_data, original_token):
    picture_id = request.form.get('picture_id', type=str)
    table = 'picture'
    parameter = 'picture_id'
    message_enpoint = ""
    status_response = None
    status_response = ""
    message_enpoint = ""

    if not picture_id:
        return jsonify({'status' : 'error', 'message': 'Parameters not entered' }), 400

    if not exist_record_in_table(table, parameter, picture_id):
        return jsonify({'status': 'error', 'message': 'The image was not found'})
    
    cursor = None
    try:    
        cursor = mysql.connection.cursor()
        query = """
                    SELECT
                        path
                    FROM
                        picture
                    WHERE
                        picture_id = %s
                """
        cursor.execute(query, ( picture_id, ))

        path = cursor.fetchone()[0]
        if path is None:
            message_enpoint = {'status': 'error', 'message' : 'The requested image was not found, please check again'}
            return jsonify(message_enpoint), 404

        if path:
            normal_path  = os.path.abspath(os.path.normpath(path))
            if os.path.exists(normal_path):
                query = """
                            DELETE FROM
                                picture
                            WHERE
                                picture_id = %s
                        """
                cursor.execute(query, (picture_id, ))
                mysql.connection.commit()
                os.remove(normal_path)
        
            else:
                message_enpoint = {'status': 'error' , 'message': 'The requested image was not found in the file system, please check again.', 'path': normal_path}
                return jsonify(message_enpoint), 404
        else:
            return jsonify({'status' : 'error', 'message' : 'The requested image was not found in the database, please check again.'}), 404
       
        message_enpoint = {'status' : 'success', 'message' : 'Correctly deleted', 'picture_id': picture_id}
        status_response = StatusResponse.SUCCESS
        return jsonify(message_enpoint), 200

    except Exception as e:
        status_response = StatusResponse.ERROR
        message_enpoint = {'status' : 'error' , 'message' : str(e)}
        return jsonify(message_enpoint), 500
    
    finally:
        if cursor:
            cursor.close()
        
        register_audit(
                type_=Transaccion.DELETE, 
                request=request.url,
                message= message_enpoint,
                status= status_response,
                user_id=token_data['user_id'], 
                entity=Table.picture
        )
    