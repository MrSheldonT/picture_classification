from flask import Flask
from app.extensions import mysql, bcrypt
from src.app.config import Config
import logging
from flask_cors import CORS

logging.basicConfig(level=logging.DEBUG)
def create_app():
    
    app = Flask(__name__)
    
    app.config.from_object(Config)
    def init_db():
        with app.app_context():
            with open("sql_definition/structure_database.sql") as f:
                mysql.engine.execute(f.read())
    mysql.init_app(app)
    bcrypt.init_app(app)
    CORS(app)
    from routes.picture_blueprint import pictures_bp
    from src.routes.ratings_blueprint import ratings_bp
    from src.routes.tags_and_categories_blueprint import tags_and_categories_bp
    from src.routes.users_blueprint import users_bp
    from src.routes.project_structure_blueprint import project_structure_bp
    with app.app_context():
        app.register_blueprint(pictures_bp)
        app.register_blueprint(ratings_bp)
        app.register_blueprint(tags_and_categories_bp)
        app.register_blueprint(users_bp)
        app.register_blueprint(project_structure_bp)
        
        
    @app.route('/')
    def index():        
        return """
<pre>
·▄▄▄▄         ▐ ▄  ▄▄▄ .
██▪ ██ ▪     •█▌▐█ ▀▄.▀·
▐█· ▐█▌ ▄█▀▄ ▐█▐▐▌▐▀▀▪▄
██. ██ ▐█▌.▐▌██▐█▌▐█▄▄▌
▀▀▀▀▀•  ▀█▄▀▪▀▀ █▪ ▀▀▀ 
</pre>
    """, 200
    
    @app.errorhandler(404)
    def global_page_not_found(e):
        return """
<pre>
 ▐ ▄       ▄▄▄▄▄    ·▄▄▄      ▄• ▄▌ ▐ ▄ ·▄▄▄▄
•█▌▐█▪     •██      ▐▄▄·▪     █▪██▌•█▌▐███▪ ██
▐█▐▐▌ ▄█▀▄  ▐█.▪    ██▪  ▄█▀▄ █▌▐█▌▐█▐▐▌▐█· ▐█▌
██▐█▌▐█▌.▐▌ ▐█▌·    ██▌.▐█▌.▐▌▐█▄█▌██▐█▌██. ██
▀▀ █▪ ▀█▄▀▪ ▀▀▀     ▀▀▀  ▀█▄▀▪ ▀▀▀ ▀▀ █▪▀▀▀▀▀•
</pre>
        """, 404

    return app