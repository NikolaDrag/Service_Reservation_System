import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY: str = os.environ.get('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI: str = os.environ.get('DATABASE_URL', 'sqlite:///reservations.db')
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    DEBUG: bool = os.environ.get('FLASK_DEBUG', '0') == '1'
