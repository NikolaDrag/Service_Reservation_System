"""
Модел за любими услуги.

Позволява на потребителите да запазват услуги като "любими"
за бърз достъп по-късно.
"""
from datetime import datetime, timezone
from db import db


class Favorite(db.Model):
    """
    Модел за любима услуга.

    Полета:
        id: Уникален идентификатор
        user_id: ID на потребителя
        service_id: ID на услугата
        created_at: Дата на добавяне

    Релации:
        user: Потребителят, който е добавил любимата
        service: Услугата, добавена като любима
    """
    __tablename__ = 'favorites'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Уникален индекс - потребител може да добави услуга само веднъж
    __table_args__ = (
        db.UniqueConstraint('user_id', 'service_id', name='unique_user_service'),
    )

    # Релации
    user = db.relationship('RegisteredUser', backref='favorites')
    service = db.relationship('Service', backref='favorited_by')

    def __init__(self, user_id: int, service_id: int):
        """
        Конструктор за Favorite.

        Параметри:
            user_id: ID на потребителя
            service_id: ID на услугата
        """
        self.user_id = user_id
        self.service_id = service_id
        self.created_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        """Връща речник с данните на любимата услуга."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'service_id': self.service_id,
            'created_at': self.created_at.isoformat(),
            'service': self.service.to_dict() if self.service else None
        }
