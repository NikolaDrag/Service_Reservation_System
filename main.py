from flask import Flask
from config import Config
from db import init_db

app: Flask = Flask(__name__)
app.config.from_object(Config)

# Импортираме моделите с новите класове
from models.user import RegisteredUser, Provider, Admin
from models.reservation import Reservation
from models.service import Service
from models.review import Review

init_db(app)

from routes.auth import auth_bp
from routes.services import services_bp
from routes.reservations import reservations_bp
from routes.reviews import reviews_bp
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(services_bp, url_prefix='/api/services')
app.register_blueprint(reservations_bp, url_prefix='/api/reservations')
app.register_blueprint(reviews_bp, url_prefix='/api/reviews')


@app.route('/')
def index() -> str:
    return "Система за управление на резервации"


if __name__ == '__main__':
    app.run(debug=True)
