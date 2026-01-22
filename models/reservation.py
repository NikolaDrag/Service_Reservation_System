from datetime import datetime
from enum import Enum
from db import db

class ReservationStatus(Enum):
    PENDING = "Pending"
    CONFIRMED = "Confirmed"
    CANCELED = "Canceled"
    COMPLETED = "Completed"

class Reservation(db.Model):
    """Резервация за услуга в сервиз"""
    __tablename__ = 'reservations'

    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.Enum(ReservationStatus), nullable=False, default=ReservationStatus.PENDING)
    notes = db.Column(db.Text, nullable=True)

    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    provider_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)

    #за улеснен достъп - дават съответно Service и User обектите
    service = db.relationship('Service', backref='reservations')
    provider = db.relationship('User', foreign_keys=[provider_id], backref='provided_reservations')

