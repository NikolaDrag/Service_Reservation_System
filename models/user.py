from enum import Enum
from db import db


class UserRole(Enum):
    USER = "user"
    PROVIDER = "provider"
    ADMIN = "admin"


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.USER)

    reservations = db.relationship('Reservation', foreign_keys='Reservation.customer_id', backref='customer', lazy=True)
    services = db.relationship('Service', backref='provider', lazy=True)
    reviews = db.relationship('Review', backref='author', lazy=True)

