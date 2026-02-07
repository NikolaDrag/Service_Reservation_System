from typing import Optional
from db import db


class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)

    def __init__(self, rating: int, user_id: int, service_id: int, comment: Optional[str] = None):
        """
        Конструктор за Review.

        Параметри:
            rating: Оценка (1-5)
            user_id: ID на потребителя, който оставя ревюто
            service_id: ID на услугата
            comment: Коментар (незадължително)
        """
        self.rating = rating
        self.comment = comment
        self.user_id = user_id
        self.service_id = service_id
