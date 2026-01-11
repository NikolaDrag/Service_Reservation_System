from flask import Flask
from config import Config
from db import db, init_db

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

from models.user import User
from models.reservation import Reservation
from models.service import Service
from models.review import Review

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return "Система за управление на резервации"

if __name__ == '__main__':
    app.run(debug=True)
