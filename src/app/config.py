import os
class Config:
    MYSQL_HOST = '127.0.0.1'
    MYSQL_DB = 'picture_classification'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True


    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'pictures')