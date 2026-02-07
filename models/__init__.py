"""
Модели за системата за управление на резервации.

Класове:
    Guest - Нерегистриран потребител (базов клас)
    RegisteredUser - Регистриран потребител
    Provider - Доставчик на услуги
    Admin - Администратор

    Service - Услуга
    Reservation - Резервация
    Review - Ревю
    Favorite - Любима услуга
    Notification - Известие

    UserRole - Enum за ролите
    ReservationStatus - Enum за статусите на резервации
    NotificationType - Enum за типовете известия
"""

from models.user import Guest, RegisteredUser, Provider, Admin, UserRole
from models.service import Service
from models.reservation import Reservation, ReservationStatus
from models.review import Review
from models.favorite import Favorite
from models.notification import Notification, NotificationType

__all__ = [  # __all__ определя какво се експортира при from models import *
    'Guest',
    'RegisteredUser',
    'Provider',
    'Admin',
    'UserRole',
    'Service',
    'Reservation',
    'ReservationStatus',
    'Review',
    'Favorite',
    'Notification',
    'NotificationType'
]
