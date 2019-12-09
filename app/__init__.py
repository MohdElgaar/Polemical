from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from flask_moment import Moment

# ------- Standard Lib -------
import os

db = SQLAlchemy()
login = LoginManager()
login.login_view = 'main.login'
migrate = Migrate()
bootstrap = Bootstrap()
moment = Moment()

def app_factory(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    login.init_app(app)
    migrate.init_app(app, db)
    bootstrap.init_app(app)
    moment.init_app(app)

    # ------ Blueprints ---------
    from app.main import main_bp 
    app.register_blueprint(main_bp)



    return app