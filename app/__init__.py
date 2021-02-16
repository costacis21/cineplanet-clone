from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_admin import Admin
from flask_login import LoginManager
import logging

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

app.config.from_pyfile('config.py')
db = SQLAlchemy(app)

migrate = Migrate(app, db, render_as_batch=True)
admin = Admin(app,template_mode='bootstrap3')

#login = LoginManager()  #Initialise login manager   <-- Uncomment when login option built
#login.init_app(app)

logging.basicConfig(level=logging.DEBUG)

from app import views, models
