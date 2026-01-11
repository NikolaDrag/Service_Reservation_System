from datetime import datetime
from enum import Enum
from typing import Optional

class ReservationStatus(Enum):
    PENDING = "Pending"
    CONFIRMED = "Confirmed"
    CANCELED = "Canceled"
    COMPLETED = "Completed"

class Reservation:
    """Резервация: Отделна страница за всяка резервация,
    Уникален идентификатор, Дата и час на резервацията,
    Статус (напр. "Очаква потвърждение", "Потвърдена", "Отменена", "Завършена"),
    Клиент (потребител, който прави резервацията), Доставчик на услуга/обект, услуга,
    Допълнителни бележки, Може да включва избрани услуги/продукти"""

    def __init__(self, id: int, datetime: datetime, status: ReservationStatus, customer_id: int,
                provider_id: int, service_id: int, notes: Optional[str] = None) -> None:
        """Инициализация на резервация"""
        self.id = id
        self.datetime = datetime
        self.status = status
        self.customer_id = customer_id
        self.provider_id = provider_id
        self.service_id = service_id
        self.notes = notes
