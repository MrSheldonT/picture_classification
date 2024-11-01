
from flask import current_app, url_for
import hashlib
import os
import mimetypes
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}
ALLOWED_MIME_TYPES = {'image/jpeg', 'image/png', 'image/gif'}

def allowed_file(filename):
     return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def picture_to_hash(file_content):
    return hashlib.sha256(file_content).hexdigest()

def save_picture(file, picture_id, upload_folder):
    
    file_extension = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{picture_id}.{file_extension}"

    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    
    return filepath

def get_mime_type(filename):
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type

def delete_picture_file(file, picture_id, upload_folder):

    file_extension = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{picture_id}.{file_extension}"
    filepath = os.path.join(upload_folder, filename)
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False

def url_for_picture(full_path):
    filename = os.path.basename(full_path)
            
    upload_folder = current_app.config['UPLOAD_FOLDER']  

    if os.path.exists(os.path.join(upload_folder, filename)):
        picture_url = url_for('pictures.serve_image', filename=filename, _external=True)
        return picture_url
    else:
        return None
    
