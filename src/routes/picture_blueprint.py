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

@pictures_bp.route('/download_picture_zip', methods=['GET'])
@token_required
def download_picture_zip():

    date_begin = request.args.get('date_begin', type=str, default='2000-01-01')
    date_end = request.args.get('date_end', type=str, default=datetime.today().strftime('%Y-%m-%d'))
    # las fechas siempre estarán
    tags = request.args.getlist('tags', type=int) # si no hay ratings(valor score), debo conectar de algún modo los ratings, por ende ratings toma de [0.0 - 3.0]
    albums = request.args.getlist('albums', type=int) # Si no hay, debo conseguirlo con get_albums by location
    locations = request.args.getlist('locations', type=int) #Si no hay, debo conseguirlo con get_locations by project
    projects = request.args.getlist('projects', type=int) # No es estrictamente necesario, pero deberá de existir album por lo menos si desears filtrar, de lo contrario enseñará todo
    scores = request.args.getlist('scores', type=float) # Nada que aclarar, solo son valores del [0.0 - 3.0]

    quantity = request.args.get('quantity', default=100, type=int)

    try:
        result = build_query(date_begin=date_begin, date_end=date_end, tags=tags, albums=albums, locations=locations, projects=projects, scores=scores, params_order="", quantity=quantity )
        
        path_pictures = result['filter_images']
        
        if not path_pictures:
            return jsonify({"status": StatusResponse.SUCCESS.value ,"message": "No pictures found for the specified filters."}), 404

        name_zip = '[' + str(date_begin) + ']' + '[' + str(date_end)  + ']' 
        name_zip += ( '[' + "_".join(tags) + ']' ) if tags else "" 
        name_zip += ( '[' + "_".join(albums) + ']' ) if albums else "" 
        name_zip += ( '[' + "_".join(locations) + ']' ) if locations else "" 
        name_zip += ( '[' + "_".join(projects) + ']' ) if projects else "" 
        name_zip += ( '[' + "_".join(scores) + ']' ) if scores else ""
        print(path_pictures)
        zip_file = pictures_to_zip(path_pictures)
        return send_file(
            zip_file,
            as_attachment=True,
            download_name=f'{name_zip}.zip',
            mimetype='application/zip'
        )
    except Exception as e:
        return jsonify({"status": StatusResponse.ERROR  ,"message": str(e)})

@pictures_bp.route('/show_path_picture', methods = ['GET'])
@token_required
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
                        , a.name
                        , l.name
                        , pr.name
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
            "project_id": result[3],
            "album_name": result[4],
            "location_name": result[5],
            "project_name": result[6]
        }

        return jsonify({"status": StatusResponse.SUCCESS.value, "image": response_data})

    except Exception as e:
        return jsonify({"status": StatusResponse.ERROR.value, "message": str(e)})
    finally:
        cursor.close()

@pictures_bp.route('/show_picture', methods=['GET'])
@token_required
def show_picture():
   
    date_begin = request.args.get('date_begin', type=str, default='2000-01-01')
    date_end = request.args.get('date_end', type=str, default=datetime.today().strftime('%Y-%m-%d'))
    tags = request.args.getlist('tags', type=int) # si no hay ratings(valor score), debo conectar de algún modo los ratings, por ende ratings toma de [0.0 - 3.0]
    albums = request.args.getlist('albums', type=int) # Si no hay, debo conseguirlo con get_albums by location
    locations = request.args.getlist('locations', type=int) #Si no hay, debo conseguirlo con get_locations by project
    projects = request.args.getlist('projects', type=int) # No es estrictamente necesario, pero deberá de existir album por lo menos si desears filtrar, de lo contrario enseñará todo
    rating = request.args.get('rating', type=int, default=1)
    scores = request.args.getlist('scores', type=float) # Nada que aclarar, solo son valores del [0.0 - 3.0]
    params_order = request.args.get('order', type=str) # Manera de ordenar, desc/asc por fecha y score, no puedes ordenar por score si no existe score wei

    page = request.args.get('page', default=1, type=int)
    quantity = request.args.get('quantity', default=100, type=int)

    try:
        
        result = build_query(date_begin=date_begin, date_end=date_end, tags=tags, albums=albums, locations=locations, projects=projects, scores=scores, params_order=params_order, quantity=quantity, ratings=rating, page=page )
        
        total_results = result['total_results']
        filter_images = result['filter_images']
        order_clause = result['order_clause']
        
        for image in filter_images:
            image['url'] = url_for_picture(image['path'])
            image['id'] = image['picture_id'] # esto pq merlin no quiere usar picture_id cawn
        total_pages = (total_results) // quantity  
        print(quantity)

        return jsonify({
            "status": StatusResponse.SUCCESS.value,
            "total_results": total_results,
            "total_pages": total_pages,
            "filtered_pictures": filter_images,
            "filter_params": {
                "date_begin": str(date_begin),
                "date_end": str(date_end),
                "tags": tags,
                "albums": albums,
                "locations": locations,
                "projects": projects,
                "ratings": scores,
                "order": order_clause,
                "page":page,
                "quantity": quantity

            }
        }), 200

    except Exception as e:
          return jsonify({"status": StatusResponse.ERROR.value, "message": str(e)}), 500

def get_locations_by_project(projects_id):
    if not projects_id:
        raise ValueError("Project IDs are required.")

    cursor = mysql.connection.cursor()
    query = """
        SELECT DISTINCT l.location_id
        FROM project AS p
        INNER JOIN location AS l ON p.project_id = l.project_id
        WHERE p.project_id IN (%s)
    """ % ', '.join(['%s'] * len(projects_id))
    cursor.execute(query, projects_id)
    locations = [row[0] for row in cursor.fetchall()]
    if not locations:
        locations.append(-404)
    return  locations

def get_albums_by_location(locations_id):
    if not locations_id:
        raise ValueError("Locations IDs are required")
    
    cursor = mysql.connection.cursor()
    query = """
        SELECT DISTINCT l.location_id
        FROM location AS l
        INNER JOIN album AS a ON l.location_id = a.location_id
        WHERE l.location_id IN (%s)
    """ % ', '.join(['%s'] * len(locations_id))
    cursor.execute(query, locations_id)
    albums = [row[0] for row in cursor.fetchall()]
    if not albums:
        albums.append(-404)
    return  albums


def get_pictures_by_album(albums_id):
    if not albums_id:
        raise ValueError("Albums IDs are required")
    cursor = mysql.connection.cursor()
    query = """
        SELECT DISTINCT p.picture_id
        FROM project AS p
        INNER JOIN album AS a ON a.album_id = a.album_id
        WHERE p.album_id IN (%s)
    """ % ', '.join(['%s'] * len(albums_id))
    cursor.execute(query, albums_id)
    pictures = [row[0] for row in cursor.fetchall()]
    if not pictures:
        pictures.append(-404)
    return  pictures

def build_query(albums, locations, projects, tags, scores, quantity, ratings = 1, params_order="", page=1, date_begin='2000-01-01', date_end=datetime.today().strftime('%Y-%m-%d')):
    offset = (page - 1) * quantity

    if tags and not scores:
       scores = [0, 0.5, 1, 1.5, 2, 2.5, 3 ]
    
    try:
        if projects:
            if not locations:
                locations = get_locations_by_project(projects_id=projects)

        if locations:
            if not albums:
                albums = get_albums_by_location(locations_id=locations)
        
        if projects and len(locations) == 0: # si a pesar de buscar los locations no existe nada, significa que o le das un proyecto que no tiene nada o que no tienen nada dentro
                locations.append(-1)
        if locations and len(albums) == 0:
                albums.append(-1)
        if date_end < date_begin:
                return jsonify({"status": StatusResponse.ERROR, "message": "Start date cannot be after end date."}), 400
    
    except Exception as e:
        return jsonify({"error": str(e)})
    try:

        try:
            date_begin = datetime.strptime(date_begin, '%Y-%m-%d').date()
            date_end = datetime.strptime(date_end, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"status": StatusResponse.ERROR, "message": "Dates must be in YYYY-MM-DD format."}), 400

        if scores:
            valid_order_options = {
                "rating asc": "r.score ASC",
                "rating desc": "r.score DESC",
                "date asc": "p.date ASC",
                "date desc": "p.date DESC"
            }
        else:
            valid_order_options = {
                "date asc": "p.date ASC",
                "date desc": "p.date DESC"
            }

        order_clause = valid_order_options.get(params_order.lower()) if params_order else ""
        
        base_query_select = "FROM picture AS p"
        column  = ["p.picture_id", "p.path", "p.date"]
        joins = []
        where_clauses = ["p.date BETWEEN %s AND %s"]
        params = [date_begin, date_end]
     
        if albums:
            joins.append("INNER JOIN album AS a ON p.album_id = a.album_id")
            where_clauses.append(f"a.album_id IN ({', '.join(['%s'] * len(albums))})")
            column.append("a.album_id")
            params.extend(albums)

        if locations:
            joins.append("INNER JOIN location AS l ON a.location_id = l.location_id")
            where_clauses.append(f"l.location_id IN ({', '.join(['%s'] * len(locations))})")
            column.append("l.location_id")
            params.extend(locations)
        
        if projects:
            joins.append("INNER JOIN project AS proj ON l.project_id = proj.project_id")
            where_clauses.append(f"proj.project_id IN ({', '.join(['%s'] * len(projects))})")
            column.append("proj.project_id")
            params.extend(projects)

        if  ratings == 0:
            joins.append("LEFT JOIN rating AS r ON r.picture_id = p.picture_id ")
            where_clauses.append("r.rating_id IS NULL")
            column.append("r.rating_id")
    
        if scores and ratings:
            joins.append("INNER JOIN rating AS r ON r.picture_id = p.picture_id")
            where_clauses.append(f"r.score IN ({', '.join(['%s'] * len(scores))})")
            column.append("r.rating_id")
            column.append("r.score")
            params.extend(scores)
        
        if tags:
            joins.append("INNER JOIN tag AS t ON t.tag_id = r.tag_id")
            where_clauses.append(f"t.tag_id IN ({', '.join(['%s'] * len(tags))})")
            column.append("t.tag_id")
            params.extend(tags)

        cursor = mysql.connection.cursor()

        select_query = f"""
        SELECT {', '.join(column)}
        {base_query_select} {' '.join(joins)} WHERE {' AND '.join(where_clauses)}
        """        
        
        count_query = f"SELECT COUNT(*) FROM ({select_query}) as count_query"
        print(select_query, count_query)                
        cursor.execute(count_query, params)
        total_results = cursor.fetchone()[0]

        if order_clause:
            select_query += f"ORDER BY {order_clause}"

        select_query += " LIMIT %s OFFSET %s"
        params.append(quantity)
        params.append(offset)
                
        cursor.execute(select_query, params)   
        images = cursor.fetchall()
                
        filter_images = []
        processed_columns = [col.split('.', 1)[1] for col in column]
        
        filter_images = []
        for row in images:
            temp = {}
            for i in range(len(processed_columns)):
                temp[processed_columns[i]] = row[i]
            filter_images.append(temp)        
        
        return {"total_results": total_results, "order_clause" : order_clause, "filter_images": filter_images }
    except Exception as e:
        print(str(e))
        return {"status": StatusResponse.ERROR.value, "message":str(e)}