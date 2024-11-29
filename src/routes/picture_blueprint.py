from flask import Blueprint, jsonify, request, current_app, send_from_directory, send_file
from utils.token_validation import token_required
from app.extensions import mysql
from utils.files import allowed_file, picture_to_hash, save_picture, delete_picture_file, url_for_picture, pictures_to_zip
from utils.database_verification import exist_record_in_table
from utils.audit import Table, StatusResponse, Transaccion, register_audit
from utils.message_status import Status
from datetime import datetime

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
    date = request.form.get('date',type=str, default=datetime.today().strftime('%Y-%m-%d'))
    table = "picture"
    parameter = "picture_id"
    
    if not album_id:
        return jsonify({'status': StatusResponse.ERROR.value, 'message' : Status.NOT_ENTERED.value, 'album_id' : album_id }), 400

    try:
        date = datetime.fromisoformat(date.replace("Z", "+00:00"))  # Si la fecha está en UTC
    except ValueError:
        return jsonify({'status': StatusResponse.ERROR.value, 'message': 'Invalid date format, should be ISO 8601'}), 400


    if file and allowed_file(file.filename):
        file_content = file.read()
        picture_id = picture_to_hash(file_content)
        file.seek(0)

        if exist_record_in_table(table, parameter,picture_id):
            return jsonify({'status' : StatusResponse.ERROR.value, 'message' : 'Image alredy exists'}), 409

        cursor = mysql.connection.cursor()
        upload_folder = current_app.config['UPLOAD_FOLDER']    
        
        try:   
            
            filepath =  save_picture(file, picture_id, upload_folder)
            query = """
                        INSERT INTO 
                            picture (picture_id, path, album_id, date)
                        VALUES (%s, %s, %s, %s)
                    """
            
            cursor.execute(query, (picture_id, filepath, album_id,date))
            mysql.connection.commit()
            status_response = StatusResponse.SUCCESS
            message_enpoint = {'status': StatusResponse.SUCCESS.value, 'message': 'Record was saved correctly', 'picture_id' : picture_id, 'filepath' : filepath, 'album_id': album_id}
            return jsonify(message_enpoint), 200
        
        except Exception as e:
            delete_picture_file(file, picture_id, upload_folder)
            status_response = StatusResponse.ERROR
            message_enpoint = {'status': StatusResponse.ERROR.value, 'message': str(e) }
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
        return jsonify({'status': StatusResponse.ERROR.value, 'message':'File type not allowed' , 'file' : file.filename }), 400

@pictures_bp.route('/uploads/<filename>')
def serve_image(filename):
    upload_folder = current_app.config['UPLOAD_FOLDER']
    return send_from_directory(upload_folder, filename)

@pictures_bp.route('/picture', methods=['GET'])
@token_required
def render_picture(token_data, original_token):

    picture_id = request.args.get('picture_id', type=str)
    
    if not picture_id:
        return jsonify({'status': StatusResponse.ERROR.value, 'message': 'No image entered'}), 400

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
            if url_picture:
                return jsonify({'status': StatusResponse.SUCCESS.value, 'picture_url': url_picture}), 200
            else:
                return jsonify({'status': StatusResponse.ERROR.value, 'message': 'File not found on the server'}), 404
        else:
            return jsonify({'status': StatusResponse.ERROR.value, 'message': 'Image with the provided ID was not found'}), 404

    except Exception as e:
        return jsonify({'status': StatusResponse.ERROR.value, 'message': str(e)}), 500
    
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
            return jsonify({'status': StatusResponse.SUCCESS.value, 'message' : Status.SUCCESSFULLY_CONSULTED.value, 'response' : url_all_pictures}), 200
        else:
            return jsonify({'status': StatusResponse.SUCCESS.value, 'message' : 'Consulted correctly, but there are no images', 'response' : url_all_pictures}), 200
    except Exception as e:
        return jsonify({'status': StatusResponse.ERROR.value, 'message' : str(e) }), 500

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
        return jsonify({'status' : StatusResponse.ERROR.value, 'message': 'Parameters not entered' }), 400

    if not exist_record_in_table(table, parameter, picture_id):
        return jsonify({'status': StatusResponse.ERROR.value, 'message': 'The image was not found'})
    
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
            message_enpoint = {'status': StatusResponse.ERROR.value, 'message' : 'The requested image was not found, please check again'}
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
                message_enpoint = {'status': StatusResponse.ERROR.value , 'message': 'The requested image was not found in the file system, please check again.', 'path': normal_path}
                return jsonify(message_enpoint), 404
        else:
            return jsonify({'status' : StatusResponse.ERROR.value, 'message' : 'The requested image was not found in the database, please check again.'}), 404
       
        message_enpoint = {'status' : StatusResponse.SUCCESS.value, 'message' : 'Correctly deleted', 'picture_id': picture_id}
        status_response = StatusResponse.SUCCESS
        return jsonify(message_enpoint), 200

    except Exception as e:
        status_response = StatusResponse.ERROR
        message_enpoint = {'status' : StatusResponse.ERROR.value , 'message' : str(e)}
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

@pictures_bp.route('/download_picture_zip_filters', methods=['POST'])

def download_picture_zip_filters():
    date_begin = request.form.get('date_begin', type=str, default='2000-01-01')
    date_end = request.form.get('date_end', type=str, default=datetime.today().strftime('%Y-%m-%d'))
    tags = request.form.getlist('tags', type=int)
    albums = request.form.getlist('albums', type=int)
    locations = request.form.getlist('locations', type=int)
    projects = request.form.getlist('projects', type=int)
    scores = request.form.getlist('scores', type=int)
    params_order = request.form.get('order', type=str)
    page = request.form.get('page', default=1, type=int)
    max_groups = request.form.get('max_groups', default=100, type=int)
    offset = (page - 1) * max_groups

    try:
        
        if scores and not tags:
            return jsonify({"status": "error", "message": "You must enter tags to filter scores."}), 400

        try:
            date_begin = datetime.strptime(date_begin, '%Y-%m-%d').date()
            date_end = datetime.strptime(date_end, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"status": "error", "message": "Dates must be in YYYY-MM-DD format."}), 400

        if date_end < date_begin:
            return jsonify({"status": "error", "message": "Start date cannot be after end date."}), 400

        valid_order_options = {
            "r.rating asc": "r.rating ASC",
            "r.rating desc": "r.rating DESC",
            "p.date asc": "p.date ASC",
            "p.date desc": "p.date DESC"
        }
        order_clause = valid_order_options.get(params_order.lower()) if params_order else ""

        cursor = mysql.connection.cursor()

        base_query = "FROM picture AS p"
        joins = []
        where = " WHERE p.date BETWEEN %s AND %s"
        params = [date_begin, date_end]

        if scores and tags:
            joins.append("""
                INNER JOIN rating AS r ON r.picture_id = p.picture_id
                INNER JOIN tag AS t ON t.tag_id = r.tag_id
            """)
            where += f" AND r.score IN ({', '.join(['%s'] * len(scores))})"
            where += f" AND t.tag_id IN ({', '.join(['%s'] * len(tags))})"
            params.extend(scores + tags)

        if locations:
            joins.append("INNER JOIN location AS l ON l.location_id = l.location_id")
            where += f" AND l.location_id IN ({', '.join(['%s'] * len(locations))})"
            params.extend(locations)

        if albums:
            joins.append("INNER JOIN album AS a ON p.album_id = a.album_id")
            where += f" AND a.album_id IN ({', '.join(['%s'] * len(albums))})"
            params.extend(albums)

        if projects:
            joins.append("INNER JOIN project AS proj ON proj.project_id = proj.project_id")
            where += f" AND proj.project_id IN ({', '.join(['%s'] * len(projects))})"
            params.extend(projects)


        select_query = f"""
            SELECT p.path, p.date, p.album_id
            {base_query} {' '.join(joins)} {where}
        """
        if order_clause:
            select_query += f" ORDER BY {order_clause}"
        select_query += " LIMIT %s OFFSET %s"
        params.extend([max_groups, offset])

        cursor.execute(select_query, params)
        results = cursor.fetchall()

        path_pictures = [{"path_os": path[0], "date": path[1], "album": path[2]} for path in results]
        if not path_pictures:
            return jsonify({"status": StatusResponse.SUCCESS.value ,"message": "No pictures found for the specified filters."}), 404
        print(len(path_pictures))
        result = '_'.join(str(e).replace(' ', '_') for e in params)
        zip_file = pictures_to_zip(path_pictures)

        return send_file(
            zip_file,
            as_attachment=True,
            download_name=f'{result}.zip',
            mimetype='application/zip'
        )
    except Exception as e:
        1
@pictures_bp.route('/show_picture', methods=['POST'])
def show_picture():
    date_begin = request.form.get('date_begin', type=str, default='2000-01-01')
    date_end = request.form.get('date_end', type=str, default=datetime.today().strftime('%Y-%m-%d'))
    tags = request.form.getlist('tags', type=int)
    albums = request.form.getlist('albums', type=int)
    locations = request.form.getlist('locations', type=int)
    projects = request.form.getlist('projects', type=int)
    scores = request.form.getlist('scores', type=int)
    params_order = request.form.get('order', type=str)
    page = request.form.get('page', default=1, type=int)
    max_groups = request.form.get('max_groups', default=100, type=int)
    offset = (page - 1) * max_groups

    try:
        
        if scores and not tags:
            return jsonify({"status": "error", "message": "You must enter tags to filter scores."}), 400

        try:
            date_begin = datetime.strptime(date_begin, '%Y-%m-%d').date()
            date_end = datetime.strptime(date_end, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"status": "error", "message": "Dates must be in YYYY-MM-DD format."}), 400

        if date_end < date_begin:
            return jsonify({"status": "error", "message": "Start date cannot be after end date."}), 400

        valid_order_options = {
            "r.rating asc": "r.rating ASC",
            "r.rating desc": "r.rating DESC",
            "p.date asc": "p.date ASC",
            "p.date desc": "p.date DESC"
        }
        order_clause = valid_order_options.get(params_order.lower()) if params_order else ""

        cursor = mysql.connection.cursor()

        base_query = "FROM picture AS p"
        joins = []
        where = " WHERE p.date BETWEEN %s AND %s"
        params = [date_begin, date_end]

        if scores and tags:
            joins.append("""
                INNER JOIN rating AS r ON r.picture_id = p.picture_id
                INNER JOIN tag AS t ON t.tag_id = r.tag_id
            """)
            where += f" AND r.score IN ({', '.join(['%s'] * len(scores))})"
            where += f" AND t.tag_id IN ({', '.join(['%s'] * len(tags))})"
            params.extend(scores + tags)

        if locations:
            joins.append("INNER JOIN location AS l ON l.location_id = l.location_id")
            where += f" AND l.location_id IN ({', '.join(['%s'] * len(locations))})"
            params.extend(locations)

        if albums:
            joins.append("INNER JOIN album AS a ON p.album_id = a.album_id")
            where += f" AND a.album_id IN ({', '.join(['%s'] * len(albums))})"
            params.extend(albums)

        if projects:
            joins.append("INNER JOIN project AS proj ON proj.project_id = proj.project_id")
            where += f" AND proj.project_id IN ({', '.join(['%s'] * len(projects))})"
            params.extend(projects)


        count_query = f"SELECT COUNT(*) {base_query} {' '.join(joins)} {where}"
        cursor.execute(count_query, params)
        total_results = cursor.fetchone()[0]

        select_query = f"""
            SELECT p.path, p.date
            {base_query} {' '.join(joins)} {where}
        """
        if order_clause:
            select_query += f" ORDER BY {order_clause}"
        select_query += " LIMIT %s OFFSET %s"
        params.extend([max_groups, offset])

        cursor.execute(select_query, params)
        results = cursor.fetchall()

        path_pictures = [{"url": url_for_picture(path[0]), "date": path[1]} for path in results]
        total_pages = (total_results + max_groups - 1) // max_groups  

        if not path_pictures:
            return jsonify({
                "status": "success",
                "message": "No images found for the specified filters."
            }), 404

        return jsonify({
            "status": "success",
            "total_pages": total_pages,
            "filtered_pictures": path_pictures,
            "filter_params": {
                "date_begin": str(date_begin),
                "date_end": str(date_end),
                "tags": tags,
                "albums": albums,
                "locations": locations,
                "projects": projects,
                "scores": scores,
                "order": params_order
            }
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@pictures_bp.route('/show_path_picture', methods = ['GET'])

def show_path_picture():
    picture_id = request.args.get('picture_id')
    
    if not picture_id:
        return jsonify({"status":StatusResponse.ERROR.value, "message": Status.NOT_ENTERED.value})
    cursor = ""
    try:
        cursor = mysql.connection.cursor()

        query = """
                    SELECT
                        p.picture_id
                        , a.album_id
                        , l.location_id
                        , pr.project_id
                    FROM
                        picture AS p
                        JOIN album AS a
                        ON a.album_id = p.album_id
                        JOIN location AS l
                        ON l.location_id = a.location_id
                        JOIN project AS pr
                        ON pr.project_id = l.location_id 
                    WHERE
                        p.picture_id = %s
                """
        
        cursor.execute(query, (picture_id,))
        result = cursor.fetchone()
        if not result:
            return jsonify({"status": StatusResponse.ERROR.value, "message": Status.RECORD_NOT_FOUND.value})

        response_data = {
            "picture_id": result[0],
            "album_id": result[1],
            "location_id": result[2],
            "project_id": result[3]
        }

        return jsonify({"status": StatusResponse.SUCCESS.value, "image": response_data})

    except Exception as e:
        return jsonify({"status": StatusResponse.ERROR.value, "message": str(e)})
    finally:
        cursor.close()
    # date_begin -> fecha normal
    # date_end -> fecha normal
    # tag = ('tag_1', 'tag_2', ... ) | ()
    # category = ('tag_1', 'tag_2', ... ) | () pero con category
    # project = ('tag_1', 'tag_2', ... ) | () pero con project
    # score_allow = (1,2,3) | ()