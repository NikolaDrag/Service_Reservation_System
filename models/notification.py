"""
Модел за известия (notifications).

Позволява системата да изпраща известия на потребителите
за нови резервации, промени в статуса, отговори и други.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from db import db


class NotificationType(Enum):
    """Типове известия."""
    RESERVATION_NEW = "new_reservation"          # Нова резервация (за provider)
    RESERVATION_CONFIRMED = "confirmed"          # Резервацията е потвърдена (за user)
    RESERVATION_CANCELLED = "cancelled"          # Резервацията е отменена
    RESERVATION_COMPLETED = "completed"          # Резервацията е завършена
    RESERVATION_REMINDER = "reminder"            # Напомняне за предстояща резервация
    NEW_REVIEW = "new_review"                    # Ново ревю за услуга (за provider)
    SYSTEM = "system"                            # Системно съобщение


class Notification(db.Model):
    """
    Модел за известие.

    Полета:
        id: Уникален идентификатор
        user_id: ID на потребителя получател
        type: Тип на известието
        title: Заглавие
        message: Съдържание на съобщението
        is_read: Дали е прочетено
        created_at: Дата на създаване
        related_id: ID на свързан обект (резервация, ревю и т.н.)
    """
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.Enum(NotificationType), nullable=False, default=NotificationType.SYSTEM)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    related_id = db.Column(db.Integer, nullable=True)  # ID на резервация, ревю и т.н.

    # Релации
    user = db.relationship('RegisteredUser', backref='notifications')

    def __init__(self, user_id: int, title: str, message: str,
                 notification_type: NotificationType = NotificationType.SYSTEM,
                 related_id: Optional[int] = None):
        """
        Конструктор за Notification.

        Параметри:
            user_id: ID на потребителя получател
            title: Заглавие на известието
            message: Съдържание
            notification_type: Тип на известието
            related_id: ID на свързан обект (незадължително)
        """
        self.user_id = user_id
        self.title = title
        self.message = message
        self.type = notification_type
        self.related_id = related_id
        self.is_read = False
        self.created_at = datetime.now(timezone.utc)

    def mark_as_read(self) -> None:
        """Маркира известието като прочетено."""
        self.is_read = True

    def to_dict(self) -> dict:
        """Връща речник с данните на известието."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type.value,
            'title': self.title,
            'message': self.message,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat(),
            'related_id': self.related_id
        }

    @classmethod
    def create_reservation_notification(cls, user_id: int, reservation_id: int,
                                         notification_type: NotificationType,
                                         service_name: str) -> 'Notification':
        """
        Създава известие за резервация.

        Параметри:
            user_id: ID на потребителя
            reservation_id: ID на резервацията
            notification_type: Тип на известието
            service_name: Име на услугата

        Връща:
            Нов Notification обект
        """
        titles = {
            NotificationType.RESERVATION_NEW: "Нова резервация",
            NotificationType.RESERVATION_CONFIRMED: "Потвърдена резервация",
            NotificationType.RESERVATION_CANCELLED: "Отменена резервация",
            NotificationType.RESERVATION_COMPLETED: "Завършена резервация",
            NotificationType.RESERVATION_REMINDER: "Напомняне за резервация"
        }

        messages = {
            NotificationType.RESERVATION_NEW: f"Имате нова резервация за услуга: {service_name}",
            NotificationType.RESERVATION_CONFIRMED: f"Вашата резервация за {service_name} е потвърдена",
            NotificationType.RESERVATION_CANCELLED: f"Резервацията за {service_name} беше отменена",
            NotificationType.RESERVATION_COMPLETED: f"Обслужването за {service_name} е завършено",
            NotificationType.RESERVATION_REMINDER: f"Напомняне: имате резервация за {service_name}"
        }

        title = titles.get(notification_type, "Известие")
        message = messages.get(notification_type, f"Известие за услуга: {service_name}")

        return cls(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            related_id=reservation_id
        )
