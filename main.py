from flask import Flask
from config import Config
from db import init_db

app: Flask = Flask(__name__)
app.config.from_object(Config)

from models.user import User
from models.reservation import Reservation
from models.service import Service
from models.review import Review

init_db(app)

from routes.auth import auth_bp
app.register_blueprint(auth_bp, url_prefix='/api/auth')


@app.route('/')
def index() -> str:
    return "Система за управление на резервации"


if __name__ == '__main__':
    app.run(debug=True)
