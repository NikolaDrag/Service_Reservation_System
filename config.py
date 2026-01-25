import os


class Config:
    SECRET_KEY: str = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    SQLALCHEMY_DATABASE_URI: str = 'sqlite:///reservations.db'
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
