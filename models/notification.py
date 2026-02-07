"""Модел за известия."""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from db import db


class NotificationType(Enum):
    """Типове известия."""
    RESERVATION_CONFIRMED = "confirmed"
    RESERVATION_CANCELLED = "cancelled"
    RESERVATION_COMPLETED = "completed"
    NEW_REVIEW = "new_review"


class Notification(db.Model):
    """Известие за потребител."""
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.Enum(NotificationType), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    related_id = db.Column(db.Integer, nullable=True)

    user = db.relationship('RegisteredUser', backref='notifications')

    def __init__(self, user_id: int, message: str,
                 notification_type: NotificationType,
                 related_id: Optional[int] = None):
        self.user_id = user_id
        self.message = message
        self.type = notification_type
        self.related_id = related_id
        self.is_read = False

    def mark_as_read(self) -> None:
        """Маркира като прочетено."""
        self.is_read = True

    def to_dict(self) -> dict:
        """Връща речник с данните."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type.value,
            'message': self.message,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'related_id': self.related_id
        }
