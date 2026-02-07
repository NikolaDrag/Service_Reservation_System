"""Модел за любими услуги."""
from datetime import datetime, timezone
from db import db


class Favorite(db.Model):
    """Любима услуга на потребител."""
    __tablename__ = 'favorites'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'service_id', name='unique_user_service'),
    )

    user = db.relationship('RegisteredUser', backref='favorites')
    service = db.relationship('Service', backref='favorited_by')

    def __init__(self, user_id: int, service_id: int):
        self.user_id = user_id
        self.service_id = service_id

    def to_dict(self) -> dict:
        """Връща речник с данните."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'service_id': self.service_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
