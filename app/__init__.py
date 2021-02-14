from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_admin import Admin


app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

app.config.from_pyfile('config.py')
db = SQLAlchemy(app)

migrate = Migrate(app, db)
admin = Admin(app,template_mode='bootstrap3')

import logging
logging.basicConfig(level=logging.DEBUG)

from app import views, models