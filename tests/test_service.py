"""
Тестове за Service модела.

Тестваме:
    - Създаване на услуга
    - Конструктора (__init__)
    - to_dict() метода
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from db import db
from models.user import Provider, RegisteredUser
from models.service import Service


class TestService(unittest.TestCase):
    """Тестове за Service модела."""

    @classmethod
    def setUpClass(cls):
        """Създава тестова база данни."""
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True
        cls.app = app
        cls.app_context = app.app_context()
        cls.app_context.push()
        db.create_all()

    @classmethod
    def tearDownClass(cls):
        """Изтрива тестовата база данни."""
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()

    def setUp(self):
        """Изпълнява се ПРЕДИ всеки тест."""
        db.session.query(Service).delete()
        db.session.query(RegisteredUser).delete()
        db.session.commit()

        # Създаваме тестов доставчик
        self.provider = Provider(
            username='test_provider',
            email='provider@test.com'
        )
        self.provider.set_password('password123')
        db.session.add(self.provider)
        db.session.commit()

    def test_create_service(self):
        """Тест: Създаване на услуга с конструктора."""
        # Arrange & Act
        service = Service(
            name='Тестова услуга',
            category='Тест',
            provider_id=self.provider.id,
            description='Описание на услугата',
            price=50.0,
            duration=30
        )
        db.session.add(service)
        db.session.commit()

        # Assert
        self.assertIsNotNone(service.id)
        self.assertEqual(service.name, 'Тестова услуга')
        self.assertEqual(service.category, 'Тест')
        self.assertEqual(service.price, 50.0)
        self.assertEqual(service.duration, 30)

    def test_service_default_values(self):
        """Тест: Услуга има стойности по подразбиране."""
        # Arrange & Act
        service = Service(
            name='Минимална услуга',
            category='Тест',
            provider_id=self.provider.id
        )
        db.session.add(service)
        db.session.commit()

        # Assert
        self.assertEqual(service.price, 0.0)  # По подразбиране 0
        self.assertEqual(service.duration, 60)  # По подразбиране 60 минути

    def test_service_to_dict(self):
        """Тест: to_dict() връща речник с всички данни."""
        # Arrange
        service = Service(
            name='Услуга за тест',
            category='Категория',
            provider_id=self.provider.id,
            description='Описание',
            price=100.0,
            availability='Пон-Пет 9:00-18:00'
        )
        db.session.add(service)
        db.session.commit()

        # Act
        result = service.to_dict()

        # Assert
        self.assertEqual(result['name'], 'Услуга за тест')
        self.assertEqual(result['category'], 'Категория')
        self.assertEqual(result['description'], 'Описание')
        self.assertEqual(result['price'], 100.0)
        self.assertEqual(result['availability'], 'Пон-Пет 9:00-18:00')
        self.assertEqual(result['provider_id'], self.provider.id)

    def test_service_relationship_with_provider(self):
        """Тест: Услугата има връзка с доставчика."""
        # Arrange
        service = Service(
            name='Услуга',
            category='Кат',
            provider_id=self.provider.id
        )
        db.session.add(service)
        db.session.commit()

        # Act - достъпваме услугата от базата
        loaded_service = db.session.get(Service, service.id)

        # Assert
        self.assertEqual(loaded_service.provider_id, self.provider.id)


if __name__ == '__main__':
    unittest.main()
