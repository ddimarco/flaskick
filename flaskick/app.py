from flask import Flask

# flask-peewee database, but could be SQLAlchemy instead.
# from flask_peewee.db import Database
from flask_sqlalchemy import SQLAlchemy

DB_PATH = 'kicker.db'

app = Flask(__name__)
app.config.from_object('flaskick.config.Configuration')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + DB_PATH
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
