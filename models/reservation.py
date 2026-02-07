from datetime import datetime
from enum import Enum
from typing import Optional
from db import db


class ReservationStatus(Enum):
    PENDING = "Pending"
    CONFIRMED = "Confirmed"
    CANCELED = "Canceled"
    COMPLETED = "Completed"


class Reservation(db.Model):
    __tablename__ = 'reservations'

    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.Enum(ReservationStatus), nullable=False, default=ReservationStatus.PENDING)
    notes = db.Column(db.Text, nullable=True)

    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    provider_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)

    service = db.relationship('Service', backref='reservations')
    provider = db.relationship('RegisteredUser', foreign_keys=[provider_id], backref='provided_reservations')

    def __init__(self, datetime, customer_id: int, provider_id: int, service_id: int,
                 status: ReservationStatus = ReservationStatus.PENDING, notes: Optional[str] = None):
        """
        Конструктор за Reservation.
        
        Параметри:
            datetime: Дата и час на резервацията
            customer_id: ID на клиента
            provider_id: ID на доставчика
            service_id: ID на услугата
            status: Статус (по подразбиране PENDING)
            notes: Бележки (незадължително)
        """
        self.datetime = datetime
        self.status = status
        self.notes = notes
        self.customer_id = customer_id
        self.provider_id = provider_id
        self.service_id = service_id

