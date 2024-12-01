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

@pictures_bp.route('/show_picture_from_album', methods=['GET'])
@token_required
def show_picture_from_album(token_data, original_token):
    
    album_id = request.args.get('album_id', default=1, type=int)
    page = request.args.get('page', default=1, type=int)
    quantity = request.args.get('quantity', default=20, type=int)
    offset = (page - 1) * quantity
    
    if not album_id:
        return jsonify({'status': StatusResponse.ERROR.value, 'message': str(Status.NOT_ENTERED), 'album_id': album_id})

    cursor = None
    try:    
        cursor = mysql.connection.cursor()

        # Obtener el total de imágenes para calcular el número total de páginas
        count_query = "SELECT COUNT(*) FROM picture WHERE album_id = %s"
        cursor.execute(count_query, (album_id,))
        total_images = cursor.fetchone()[0]
        total_pages = (total_images + quantity - 1) // quantity  # Calcula el número total de páginas

        # Consulta para obtener las imágenes de la página actual
        query = """
                    SELECT 
                        path, picture_id, date
                    FROM 
                        picture 
                    WHERE 
                        album_id = %s
                    LIMIT %s 
                    OFFSET %s
                """
        
        cursor.execute(query, (album_id, quantity, offset))
        all_pictures = cursor.fetchall()
        url_all_pictures = []
        
        for picture in all_pictures:
            url_picture = (url_for_picture(picture[0]), picture[1], picture[2])
            if url_picture:
                url_all_pictures.append(url_picture)
            else:
                print("No valido.")

        if len(url_all_pictures):
            return jsonify({
                'status': StatusResponse.SUCCESS.value,
                'message': str(Status.SUCCESSFULLY_CONSULTED),
                'response': url_all_pictures,
                'total_pages': total_pages
            }), 200
        else:
            return jsonify({
                'status': StatusResponse.SUCCESS.value,
                'message': 'Consulted correctly, but there are no images',
                'response': url_all_pictures,
                'total_pages': total_pages
            }), 200
    
    except Exception as e:
        return jsonify({'status': StatusResponse.ERROR.value, 'message': str(e)}), 500

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
        return jsonify({'status': StatusResponse.ERROR.value, 'message': Status.NOT_ENTERED.value, 'location_id': location_id})
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
            return jsonify({'status': StatusResponse.SUCCESS.value, 'message' : Status.SUCCESSFULLY_CONSULTED.value, 'response' : url_all_pictures}), 200
        else:
            return jsonify({'status': StatusResponse.SUCCESS.value, 'message' : 'Consulted correctly, but there are no images', 'response' : url_all_pictures}), 200
    
    except Exception as e:
        return jsonify({'status': StatusResponse.ERROR.value, 'message' : str(e) }), 500
    
    finally:
        if cursor:
            cursor.close()


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


@pictures_bp.route('/show_picture_from_project', methods = ['GET'])
@token_required
def show_picture_from_project(token_data, original_token):

    project_id = request.args.get('project_id', type=int)
    page = request.args.get('page', default=1, type=int)
    quantity = request.args.get('quantity', default=20, type=int)
    offset = ( page - 1 ) * quantity
    
    if not project_id:
        return jsonify({'status': StatusResponse.ERROR.value, 'message': 'Parameters not entered', 'project_id': project_id})

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
            return jsonify({'status': StatusResponse.SUCCESS.value, 'message' : Status.SUCCESSFULLY_CONSULTED.value, 'response' : url_all_pictures}), 200
        else:
            return jsonify({'status': StatusResponse.SUCCESS.value, 'message' : 'Consulted correctly, but there are no images', 'response' : url_all_pictures}), 200
    
    except Exception as e:
        return jsonify({'status': StatusResponse.ERROR.value, 'message' : str(e)}), 500
    
    finally:
        if cursor:
            cursor.close()



@pictures_bp.route('/download_picture_zip', methods=['GET'])

def download_picture_zip():

    date_begin = request.args.get('date_begin', type=str, default='2000-01-01')
    date_end = request.args.get('date_end', type=str, default=datetime.today().strftime('%Y-%m-%d'))
    # las fechas siempre estarán
    tags = request.args.getlist('tags', type=int) # si no hay ratings(valor score), debo conectar de algún modo los ratings, por ende ratings toma de [0.0 - 3.0]
    albums = request.args.getlist('albums', type=int) # Si no hay, debo conseguirlo con get_albums by location
    locations = request.args.getlist('locations', type=int) #Si no hay, debo conseguirlo con get_locations by project
    projects = request.args.getlist('projects', type=int) # No es estrictamente necesario, pero deberá de existir album por lo menos si desears filtrar, de lo contrario enseñará todo
    scores = request.args.getlist('scores', type=float) # Nada que aclarar, solo son valores del [0.0 - 3.0]

    page = request.args.get('page', default=1, type=int)
    quantity = request.args.get('quantity', default=100, type=int)
    offset = (page - 1) * quantity

    if tags and not scores:
       scores = [0, 0.5, 1, 1.5, 2, 2.5, 3 ]

    if projects:
        if not locations:
            locations = get_locations_by_project(projects_id=projects)
   
    if locations:
        if not albums:
            albums = get_albums_by_location(locations_id=locations)
        
    if date_end < date_begin:
            return jsonify({"status": "error", "message": "Start date cannot be after end date."}), 400

    try:

        try:
            date_begin = datetime.strptime(date_begin, '%Y-%m-%d').date()
            date_end = datetime.strptime(date_end, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"status": "error", "message": "Dates must be in YYYY-MM-DD format."}), 400

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
        
        base_query = "FROM picture AS p"
        column  = [ "p.path", "p.date"]
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

        if scores:
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
        {base_query} {' '.join(joins)} WHERE {' AND '.join(where_clauses)}
        """
        
        params.extend([quantity, offset])
        select_query += " LIMIT %s OFFSET %s"
        cursor.execute(select_query, params)
        
        results = cursor.fetchall()
        
        path_pictures = []
        
        
        for path in results:
            picture_data = {}

            for i, attribute in enumerate(column):
                attribute = attribute.split('.')[-1]
                picture_data[attribute] = path[i]

            path_pictures.append(picture_data)
        
        if not path_pictures:
            return jsonify({"status": StatusResponse.SUCCESS.value ,"message": "No pictures found for the specified filters."}), 404
       

        result = '_'.join(str(e).replace(' ', '_') for e in params)
        print(path_pictures)
        zip_file = pictures_to_zip(path_pictures)
        return send_file(
            zip_file,
            as_attachment=True,
            download_name=f'{result}.zip',
            mimetype='application/zip'
        )
    except Exception as e:
        1


@pictures_bp.route('/show_picture', methods=['GET']) # mero mero o.o, no está terminado btw.
def show_picture():
    date_begin = request.args.get('date_begin', type=str, default='2000-01-01')
    date_end = request.args.get('date_end', type=str, default=datetime.today().strftime('%Y-%m-%d'))
    # las fechas siempre estarán
    tags = request.args.getlist('tags', type=int) # si no hay ratings(valor score), debo conectar de algún modo los ratings, por ende ratings toma de [0.0 - 3.0]
    albums = request.args.getlist('albums', type=int) # Si no hay, debo conseguirlo con get_albums by location
    locations = request.args.getlist('locations', type=int) #Si no hay, debo conseguirlo con get_locations by project
    projects = request.args.getlist('projects', type=int) # No es estrictamente necesario, pero deberá de existir album por lo menos si desears filtrar, de lo contrario enseñará todo
    scores = request.args.getlist('scores', type=float) # Nada que aclarar, solo son valores del [0.0 - 3.0]
    params_order = request.args.get('order', type=str) # Manera de ordenar, desc/asc por fecha y score, no puedes ordenar por score si no existe score wei


    page = request.args.get('page', default=1, type=int)
    quantity = request.args.get('quantity', default=100, type=int)
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
                return jsonify({"status": "error", "message": "Start date cannot be after end date."}), 400
    except Exception as e:
        return jsonify({"error": str(e)})
    try:

        try:
            date_begin = datetime.strptime(date_begin, '%Y-%m-%d').date()
            date_end = datetime.strptime(date_end, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"status": "error", "message": "Dates must be in YYYY-MM-DD format."}), 400

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
        
        base_query = "FROM picture AS p"
        column  = [ "p.path", "p.date"]
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

        if scores:
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

        
        
        count_query = f"SELECT COUNT(*) {base_query} {' '.join(joins)}  WHERE {' AND '.join(where_clauses)} "

        cursor = mysql.connection.cursor()
        cursor.execute(count_query, params)
        total_results = cursor.fetchone()[0]

        select_query = f"""
        SELECT {', '.join(column)}
        {base_query} {' '.join(joins)} WHERE {' AND '.join(where_clauses)}
        """
        if order_clause:
            select_query += f" ORDER BY {order_clause}"
        select_query += " LIMIT %s OFFSET %s"

        params.extend([quantity, offset])
        
        cursor.execute(select_query, params)
        results = cursor.fetchall()

        path_pictures = []

        for path in results:
            picture_data = {}

            for i, attribute in enumerate(column):
                attribute = attribute.split('.')[-1]
                if attribute == "path":
                    picture_data['url'] = url_for_picture(path[i])
                else:
                    picture_data[attribute] = path[i]

            path_pictures.append(picture_data)
        
        total_pages = (total_results + quantity - 1) // quantity  


        return jsonify({
            "status": StatusResponse.SUCCESS.value,
            "total_pages": total_pages,
            "filtered_pictures": path_pictures,
            "filter_params": {
                "date_begin": str(date_begin),
                "date_end": str(date_end),
                "tags": tags,
                "albums": albums,
                "locations": locations,
                "projects": projects,
                "ratings": scores,
                "order": order_clause
            }
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

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
    return [row[0] for row in cursor.fetchall()]

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
    return [row[0] for row in cursor.fetchall()]

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
    return [row[0] for row in cursor.fetchall()]
