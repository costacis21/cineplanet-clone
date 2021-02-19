import os


SQLALCHEMY_TRACK_MODIFICATIONS = True   
basedir = os.path.abspath(os.path.dirname(__file__))
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')

WTF_CSRF_ENABLED = True
SECRET_KEY = '6UDpmaGCElwWaRRWHBEQ'