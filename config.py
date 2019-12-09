import os 
app_path = os.path.abspath(os.path.dirname(__file__) )

class Config(object):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DB_URL') or 'sqlite:///' + os.path.join(app_path, 'app.db')
    SECRET_KEY = os.environ.get('SECRET_KEY') or "astrongkeyinc"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BOOTSTRAP_SERVE_LOCAL = True
    STATIC_FOLDER = 'static'
    SITE_NAME = 'Polemical'
    CURRENCY = ''
    