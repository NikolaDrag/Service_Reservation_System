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
    """
    Модел за резервация за авто сервиз.

    Полета:
        id: Уникален идентификатор
        datetime: Дата и час на резервацията
        status: Статус на резервацията
        notes: Описание на проблема (текст)
        problem_image_url: URL на снимка на проблема
        customer_id: ID на клиента
        provider_id: ID на сервиза/специалиста
        service_id: ID на услугата
    """
    __tablename__ = 'reservations'

    id = db.Column(db.Integer, primary_key=True)
    datetime = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.Enum(ReservationStatus), nullable=False, default=ReservationStatus.PENDING)
    notes = db.Column(db.Text, nullable=True)  # Описание на проблема
    problem_image_url = db.Column(db.String(500), nullable=True)  # URL на снимка на проблема

    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    provider_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)

    service = db.relationship('Service', backref='reservations')
    provider = db.relationship('RegisteredUser', foreign_keys=[provider_id], backref='provided_reservations')

    def __init__(self, datetime, customer_id: int, provider_id: int, service_id: int,
                 status: ReservationStatus = ReservationStatus.PENDING,
                 notes: Optional[str] = None, problem_image_url: Optional[str] = None):
        """
        Конструктор за Reservation.

        Параметри:
            datetime: Дата и час на резервацията
            customer_id: ID на клиента
            provider_id: ID на доставчика/сервиза
            service_id: ID на услугата
            status: Статус (по подразбиране PENDING)
            notes: Описание на проблема (незадължително)
            problem_image_url: URL на снимка на проблема (незадължително)
        """
        self.datetime = datetime
        self.status = status
        self.notes = notes
        self.problem_image_url = problem_image_url
        self.customer_id = customer_id
        self.provider_id = provider_id
        self.service_id = service_id

    def to_dict(self) -> dict:
        """Връща речник с данните на резервацията."""
        return {
            'id': self.id,
            'datetime': self.datetime.isoformat(),
            'status': self.status.value,
            'notes': self.notes,
            'problem_image_url': self.problem_image_url,
            'customer_id': self.customer_id,
            'provider_id': self.provider_id,
            'service_id': self.service_id
        }

