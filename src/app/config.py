import os
class Config:
    MYSQL_HOST = '127.0.0.1'
    MYSQL_DB = 'picture_classification'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = '1430623'
    SECRET_KEY = 'MAYATOMETRO'
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'pictures')