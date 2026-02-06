from typing import Optional
from db import db


class Service(db.Model):
    """
    Модел за услуга.
    
    Полета:
        id: Уникален идентификатор
        name: Име на услугата
        description: Описание
        category: Категория
        price: Цена
        duration: Продължителност в минути
        availability: Работно време (текст)
        image_url: URL на снимка
        provider_id: ID на доставчика (собственик)
    """
    __tablename__ = 'services'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=False)
    
    # Нови полета за цена и продължителност
    price = db.Column(db.Float, nullable=True, default=0.0)
    duration = db.Column(db.Integer, nullable=True, default=60)  # В минути
    
    # Работно време - заместваме working_hours_start/end с по-гъвкаво текстово поле
    availability = db.Column(db.String(255), nullable=True)  # "Пон-Пет 9:00-18:00"
    
    # Запазваме старите полета за обратна съвместимост
    working_hours_start = db.Column(db.Time, nullable=True)
    working_hours_end = db.Column(db.Time, nullable=True)
    
    image_url = db.Column(db.String(255), nullable=True)

    provider_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    reviews = db.relationship('Review', backref='service', lazy=True)
    
    def __init__(self, name: str, category: str, provider_id: int,
                 description: Optional[str] = None, price: float = 0.0,
                 duration: int = 60, availability: Optional[str] = None,
                 image_url: Optional[str] = None):
        """
        Конструктор за Service.
        
        Параметри:
            name: Име на услугата
            category: Категория
            provider_id: ID на доставчика
            description: Описание (незадължително)
            price: Цена (по подразбиране 0.0)
            duration: Продължителност в минути (по подразбиране 60)
            availability: Работно време (незадължително)
            image_url: URL на снимка (незадължително)
        """
        self.name = name
        self.description = description
        self.category = category
        self.price = price
        self.duration = duration
        self.availability = availability
        self.image_url = image_url
        self.provider_id = provider_id
    
    def to_dict(self) -> dict:
        """Преобразува услугата в речник."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'price': self.price,
            'duration': self.duration,
            'availability': self.availability,
            'image_url': self.image_url,
            'provider_id': self.provider_id
        }
