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

@pictures_bp.route('/show_album_date_range', methods=['GET'])
@token_required
def show_album_date_range(token_data, original_token):
    
    album_id = request.args.get('album_id', type=int)
    
    if not album_id:
        return jsonify({'status': StatusResponse.ERROR.value, 'message': 'Album ID is required', 'album_id': album_id}), 400

    cursor = None
    try:    
        cursor = mysql.connection.cursor()
        
        # Consulta para obtener las fechas más antigua y más reciente
        query = """
                    SELECT 
                        MIN(date) AS earliest_date,
                        MAX(date) AS latest_date
                    FROM 
                        picture 
                    WHERE 
                        album_id = %s
                """
        
        cursor.execute(query, (album_id,))
        result = cursor.fetchone()
        
        if result and result[0] and result[1]:  # Accede a los resultados por índice
            # Devolvemos la fecha más antigua y la más reciente
            return jsonify({
                'status': StatusResponse.SUCCESS.value, 
                'message': 'Date range retrieved successfully',
                'earliest_date': result[0],  # earliest_date es el primer campo
                'latest_date': result[1]      # latest_date es el segundo campo
            }), 200
        else:
            # Caso en que no hay fotos en el álbum
            return jsonify({
                'status': StatusResponse.SUCCESS.value, 
                'message': 'No pictures found for this album', 
                'earliest_date': None, 
                'latest_date': None
            }), 200

    except Exception as e:
        return jsonify({'status': StatusResponse.ERROR.value, 'message' : str(e)}), 500

    finally:
        if cursor:
            cursor.close()

@pictures_bp.route('/show_picture_from_album_pages', methods=['GET'])
@token_required
def show_picture_from_album_pages(token_data, original_token):
    album_id = request.args.get('album_id', default=1, type=int)
    max_pictures_per_group = request.args.get('max_pictures_per_group', default=6, type=int)  # Limitar imágenes por grupo
    max_groups = request.args.get('max_groups', default=6, type=int)  # Limitar grupos (por fecha)
    page = request.args.get('page', default=1, type=int)
    
    # Definir el número de imágenes por página
    offset = (page - 1) * max_groups  # Calcular el desplazamiento para grupos

    if not album_id:
        return jsonify({'status': StatusResponse.ERROR.value, 'message': Status.NOT_ENTERED.value, 'album_id': album_id})

    cursor = None
    try:
        cursor = mysql.connection.cursor()
        
        # Consulta para obtener las imágenes del álbum ordenadas por fecha
        query = """
            SELECT 
                path, picture_id, date
            FROM 
                picture 
            WHERE 
                album_id = %s
            ORDER BY 
                date DESC
        """
        
        # Ejecutar la consulta para obtener todas las imágenes
        cursor.execute(query, (album_id,))
        all_pictures = cursor.fetchall()

        # Agrupar las imágenes por mes y año (YYYY-MM)
        pictures_by_date = {}
        for picture in all_pictures:
            path, picture_id, date = picture
            # Formato año-mes (YYYY-MM) para la agrupación
            year_month = date.strftime("%Y-%m")  # Usamos solo año y mes para agrupar
            if year_month not in pictures_by_date:
                pictures_by_date[year_month] = []
            pictures_by_date[year_month].append({
                "url": url_for_picture(path),
                "picture_id": picture_id,
                "date": date
            })

        # Limitar el número de imágenes dentro de cada grupo de fechas
        for date, pictures in pictures_by_date.items():
            pictures_by_date[date] = pictures[:max_pictures_per_group]  # Limitamos a max_pictures_per_group imágenes por grupo de fecha

        # Convertir el diccionario a una lista de grupos de imágenes (por fecha completa)
        grouped_pictures = [{"date": date, "pictures": pictures} for date, pictures in pictures_by_date.items()]

        # Ordenar los grupos por fecha (año-mes) en orden descendente
        grouped_pictures.sort(key=lambda x: x["date"], reverse=True)

        # Limitar el número de grupos que se devuelven
        grouped_pictures = grouped_pictures[offset:offset + max_groups]  # Limitamos el número de grupos devueltos para la página

        # Calcular la cantidad total de páginas necesarias
        total_groups = len(pictures_by_date)  # Total de grupos sin limitación
        total_pages = (total_groups + max_groups - 1) // max_groups  # Redondear hacia arriba

        # Obtener la sección de grupos de imágenes correspondiente a la página solicitada
        page_groups = grouped_pictures

        # Retornar la respuesta con las imágenes agrupadas por fecha en forma de matriz
        return jsonify({
            'status': StatusResponse.SUCCESS.value,
            'message': 'Pictures retrieved successfully',
            'response': page_groups,
            'total_pages': total_pages,
            'current_page': page
        }), 200

    except Exception as e:
        return jsonify({'status': StatusResponse.ERROR.value, 'message': str(e)}), 500

    finally:
        if cursor:
            cursor.close()


@pictures_bp.route('/show_picture_from_album_progress', methods=['GET'])
@token_required
def show_picture_from_album_progress(token_data, original_token):
    album_id = request.args.get('album_id', default=1, type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    max_pictures = request.args.get('max_pictures', default=10, type=int)
    page = request.args.get('page', default=1, type=int)
    offset = (page - 1) * max_pictures
    
    if not album_id:
        return jsonify({'status': StatusResponse.ERROR.value, 'message': Status.NOT_ENTERED.value, 'album_id': album_id})

    cursor = None
    try:
        cursor = mysql.connection.cursor()
        
        if start_date:
            try:
                start_date = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            except ValueError:
                return jsonify({'status': StatusResponse.ERROR.value, 'message': 'Invalid start_date format'}), 400
        
        if end_date:
            try:
                end_date = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            except ValueError:
                return jsonify({'status': StatusResponse.ERROR.value, 'message': 'Invalid end_date format'}), 400
        
        query = """
            SELECT 
                path, picture_id, date
            FROM 
                picture 
            WHERE 
                album_id = %s
        """
        
        params = [album_id]
        
        if start_date and end_date:
            query += " AND date BETWEEN %s AND %s"
            params.extend([start_date, end_date])

        query += " ORDER BY date ASC LIMIT %s OFFSET %s"
        params.extend([max_pictures, offset])

        cursor.execute(query, tuple(params))
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
            return jsonify({'status': StatusResponse.SUCCESS.value, 'message': 'Pictures retrieved successfully', 'response': pictures_by_date}), 200
        else:
            return jsonify({'status': StatusResponse.SUCCESS.value, 'message': 'No pictures found', 'response': pictures_by_date}), 200

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

#deprecated
@pictures_bp.route('/download_picture_zip_filter', methods=['POST'])
@token_required
def download_picture_zip(token_data, original_token):
    date_begin = request.form.get('date_begin', type=str, default='2000-01-01')
    date_end = request.form.get('date_end', type=str, default=datetime.today().strftime('%Y-%m-%d'))
    tag = request.form.get('tag', type=int)
    category = request.form.get('category', type=int)
    project = request.form.get('project', type=int)
    score_min_rating = request.form.get('score_min_rating', type=int, default=0)
    score_max_rating = request.form.get('score_max_rating', type=int, default=3)
    
    try:
        
        cursor = mysql.connection.cursor()
        
        query = """
            SELECT
                p.path
            FROM
                picture AS p
                LEFT JOIN rating AS r
                    ON r.picture_id = p.picture_id
                LEFT JOIN album AS a
                    ON p.album_id = a.album_id
                LEFT JOIN location as l
                    ON a.location_id = l.location_id
                LEFT JOIN project as proj
                    ON proj.project_id = l.project_id
                LEFT JOIN tag AS t
                    ON t.tag_id = r.tag_id
                LEFT JOIN category AS c
                    ON c.category_id = t.category_id 
            WHERE
                p.date BETWEEN %s AND %s
        """
        params = [date_begin, date_end]
        if tag:
            query += " AND (t.tag_id = %s OR t.tag_id IS NULL)"
            params.append(tag)
        if category:
            query += " AND (c.category_id = %s OR c.category_id IS NULL)"
            params.append(category)
        if project:
            query += " AND (proj.project_id = %s OR proj.project_id IS NULL)"
            params.append(project)
        if score_min_rating is not None and score_max_rating is not None:
            query += " AND (r.score BETWEEN %s AND %s OR r.score IS NULL)"
            params.extend([score_min_rating, score_max_rating])

        cursor.execute(query, params)
        
        path_pictures = []
        for path in cursor.fetchall():
            path_pictures.append(path[0])
        
        result = '_'.join(str(e).replace(' ', '_') for e in params)
        
        zip_file = pictures_to_zip(path_pictures, result)

        return send_file(
            zip_file,
            as_attachment=True,
            download_name='pictures.zip',
            mimetype='application/zip'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()


@pictures_bp.route('/download_picture_zip_filters', methods=['POST'])
@token_required
def download_picture_zip_filters(token_data, original_token):
    date_begin = request.form.get('date_begin', type=str, default='2000-01-01')
    date_end = request.form.get('date_end', type=str, default=datetime.today().strftime('%Y-%m-%d'))
    tags = request.form.getlist('tags', type=int)
    categories = request.form.getlist('categories', type=int)
    projects = request.form.getlist('projects', type=int)
    scores = request.form.getlist('scores', type=int)
    
    print("-------------------",tags,"------------")
    try:
        cursor = mysql.connection.cursor()
        query = """
            SELECT
                p.path
            FROM
                picture AS p
                LEFT JOIN rating AS r
                    ON r.picture_id = p.picture_id
                LEFT JOIN album AS a
                    ON p.album_id = a.album_id
                LEFT JOIN location as l
                    ON a.location_id = l.location_id
                LEFT JOIN project as proj
                    ON proj.project_id = l.project_id
                LEFT JOIN tag AS t
                    ON t.tag_id = r.tag_id
                LEFT JOIN category AS c
                    ON c.category_id = t.category_id 
            WHERE
                p.date BETWEEN %s AND %s
        """ 
        params = [date_begin, date_end]
        if tags:
            query += f" AND (t.tag_id IN ({', '.join(['%s'] * len(tags))}))"
            params.extend(tags)
        if categories:
            query += f" AND (c.category_id IN ({', '.join(['%s'] * len(categories))}))"
            params.extend(categories)
        if projects:
            query += f" AND (proj.project_id IN ({', '.join(['%s'] * len(projects))}))"
            params.extend(projects)
        if scores:
            query += f" AND (r.score IN ({', '.join(['%s'] * len(scores))}))"
            params.extend(scores)
        
        
        cursor.execute(query, params)
        
        path_pictures = []
        
        for path in cursor.fetchall():
            path_pictures.append(path[0])
        
        result = '_'.join(str(e).replace(' ', '_') for e in params)
        
        zip_file = pictures_to_zip(path_pictures, result)

        return send_file(
            zip_file,
            as_attachment=True,
            download_name='task.zip',
            mimetype='application/zip'
        )
    except Exception as e:
        1
    # date_begin -> fecha normal
    # date_end -> fecha normal
    # tag = ('tag_1', 'tag_2', ... ) | ()
    # category = ('tag_1', 'tag_2', ... ) | () pero con category
    # project = ('tag_1', 'tag_2', ... ) | () pero con project
    # score_allow = (1,2,3) | ()