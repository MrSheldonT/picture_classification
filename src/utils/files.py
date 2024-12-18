
from flask import current_app, url_for
from PIL import Image
import hashlib
import zipfile
import os
import mimetypes
import io
import re
  
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}
ALLOWED_MIME_TYPES = {'image/jpeg', 'image/png', 'image/gif'}

def allowed_file(filename):
     return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def picture_to_hash(file_content):
    return hashlib.sha256(file_content).hexdigest()

def save_picture(original_file, picture_id, upload_folder,low_res_size=(800, 600)):
 
    file_extension = original_file.filename.rsplit('.', 1)[1].lower()
    filename = f"{picture_id}.{file_extension}"

    original_folder = os.path.join(upload_folder, "original")
    low_res_folder = os.path.join(upload_folder, "low_res")

    os.makedirs(original_folder, exist_ok=True)
    os.makedirs(low_res_folder, exist_ok=True)
    original_filepath = os.path.join(original_folder, filename)
    low_res_filepath = os.path.join(low_res_folder, filename)

    original_file.save(original_filepath)

    with Image.open(original_filepath) as img:

        img = img.resize(low_res_size)
        img.save(low_res_filepath, format=img.format)
    
    return {
        "original": original_filepath,
        "low_res": low_res_filepath
    }

def get_mime_type(filename):
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type

def url_for_picture(filename, type):
    filename = os.path.basename(filename)
    upload_folder = current_app.config['UPLOAD_FOLDER']

    if type == 'original':
        upload_folder = os.path.join(upload_folder, "original")
    elif type == 'low':
        upload_folder = os.path.join(upload_folder, "low_res")
    
    if os.path.exists(os.path.join(upload_folder, filename)):
        picture_url = url_for('pictures.serve_image', folder=type, filename=filename, _external=True)
        return picture_url
    else:
        return None
def sanitize_filename(filename):
    """Eliminar caracteres no válidos para nombres de archivo."""
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def pictures_to_zip(paths):
    zip_buffer = io.BytesIO()
    
    try:        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for path in paths:
                upload_folder = current_app.config['UPLOAD_FOLDER']                
                file_path_original = os.path.join(upload_folder, 'original', path["path"])
                
                if not os.path.exists(file_path_original):
                    print(f"El archivo no existe: {file_path_original}")
                    continue
                
                original_name = os.path.basename(file_path_original)                

                print(f"Agregando archivo: {file_path_original}")
                
                try:
                    zipf.write(file_path_original, arcname=original_name)
                    
                except Exception as e:
                    print(f"Error al agregar {file_path_original} al ZIP: {e}")
        
        zip_buffer.seek(0)
        
    except Exception as e:
        print(f"Error general al crear el ZIP: {e}")
    
    return zip_buffer
