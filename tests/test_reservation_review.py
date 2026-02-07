"""
Тестове за Reservation и Review моделите.
"""
import unittest
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from db import db
from models.user import RegisteredUser, Provider, UserRole
from models.service import Service
from models.reservation import Reservation, ReservationStatus
from models.review import Review


class TestReservation(unittest.TestCase):
    """Тестове за Reservation модела."""

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
        db.session.query(Review).delete()
        db.session.query(Reservation).delete()
        db.session.query(Service).delete()
        db.session.query(RegisteredUser).delete()
        db.session.commit()

        # Създаваме тестови потребители
        self.customer = RegisteredUser(
            username='customer',
            email='customer@test.com'
        )
        self.customer.set_password('pass123')

        self.provider = Provider(
            username='provider',
            email='provider@test.com'
        )
        self.provider.set_password('pass123')

        db.session.add(self.customer)
        db.session.add(self.provider)
        db.session.commit()

        # Създаваме тестова услуга
        self.service = Service(
            name='Тестова услуга',
            category='Тест',
            provider_id=self.provider.id
        )
        db.session.add(self.service)
        db.session.commit()

    def test_create_reservation(self):
        """Тест: Създаване на резервация с конструктора."""
        # Arrange
        reservation_time = datetime.now() + timedelta(days=1)

        # Act
        reservation = Reservation(
            customer_id=self.customer.id,
            service_id=self.service.id,
            provider_id=self.provider.id,
            datetime=reservation_time,
            notes='Тестова бележка'
        )
        db.session.add(reservation)
        db.session.commit()

        # Assert
        self.assertIsNotNone(reservation.id)
        self.assertEqual(reservation.status, ReservationStatus.PENDING)
        self.assertEqual(reservation.notes, 'Тестова бележка')

    def test_reservation_default_status(self):
        """Тест: Резервацията има статус PENDING по подразбиране."""
        # Arrange & Act
        reservation = Reservation(
            customer_id=self.customer.id,
            service_id=self.service.id,
            provider_id=self.provider.id,
            datetime=datetime.now()
        )
        db.session.add(reservation)
        db.session.commit()

        # Assert
        self.assertEqual(reservation.status, ReservationStatus.PENDING)

    def test_create_reservation_via_user_method(self):
        """Тест: create_reservation() метода на RegisteredUser."""
        # Arrange
        reservation_time = datetime.now() + timedelta(days=1)

        # Act - параметърът е reservation_date, не datetime_obj
        result = self.customer.create_reservation(
            service_id=self.service.id,
            reservation_date=reservation_time,
            notes='Чрез метода'
        )

        # Assert - връща Reservation обект, не речник
        self.assertIsNotNone(result)
        self.assertEqual(result.customer_id, self.customer.id)
        self.assertEqual(result.service_id, self.service.id)

    def test_get_my_reservations(self):
        """Тест: get_my_reservations() връща резервациите на потребителя."""
        # Arrange - използваме reservation_date
        self.customer.create_reservation(
            service_id=self.service.id,
            reservation_date=datetime.now() + timedelta(days=1)
        )
        self.customer.create_reservation(
            service_id=self.service.id,
            reservation_date=datetime.now() + timedelta(days=2)
        )

        # Act
        result = self.customer.get_my_reservations()

        # Assert
        self.assertEqual(len(result), 2)

    def test_cancel_reservation(self):
        """Тест: cancel_reservation() отменя резервация."""
        # Arrange
        reservation = self.customer.create_reservation(
            service_id=self.service.id,
            reservation_date=datetime.now() + timedelta(days=1)
        )

        # Act
        result = self.customer.cancel_reservation(reservation.id)

        # Assert
        self.assertTrue(result)
        cancelled = db.session.get(Reservation, reservation.id)
        assert cancelled is not None  # type guard за Pylance
        self.assertEqual(cancelled.status, ReservationStatus.CANCELED)  # CANCELED, не CANCELLED


class TestReview(unittest.TestCase):
    """Тестове за Review модела."""

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
        db.session.query(Review).delete()
        db.session.query(Service).delete()
        db.session.query(RegisteredUser).delete()
        db.session.commit()

        # Създаваме тестови потребители
        self.user = RegisteredUser(
            username='reviewer',
            email='reviewer@test.com'
        )
        self.user.set_password('pass123')

        self.provider = Provider(
            username='provider',
            email='provider@test.com'
        )
        self.provider.set_password('pass123')

        db.session.add(self.user)
        db.session.add(self.provider)
        db.session.commit()

        # Създаваме тестова услуга
        self.service = Service(
            name='Тестова услуга',
            category='Тест',
            provider_id=self.provider.id
        )
        db.session.add(self.service)
        db.session.commit()

    def test_create_review(self):
        """Тест: Създаване на ревю с конструктора."""
        # Arrange & Act
        review = Review(
            user_id=self.user.id,
            service_id=self.service.id,
            rating=5,
            comment='Отлична услуга!'
        )
        db.session.add(review)
        db.session.commit()

        # Assert
        self.assertIsNotNone(review.id)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, 'Отлична услуга!')

    def test_leave_review_via_user_method(self):
        """Тест: leave_review() метода на RegisteredUser."""
        # Act - връща Review обект
        result = self.user.leave_review(
            service_id=self.service.id,
            rating=4,
            comment='Много добра услуга'
        )

        # Assert - result е Review обект
        self.assertIsNotNone(result)
        self.assertEqual(result.rating, 4)
        self.assertEqual(result.comment, 'Много добра услуга')

    def test_leave_review_invalid_rating(self):
        """Тест: leave_review() хвърля ValueError при невалиден рейтинг."""
        # Act & Assert - очакваме ValueError
        with self.assertRaises(ValueError):
            self.user.leave_review(
                service_id=self.service.id,
                rating=6,  # Невалиден - трябва да е 1-5
                comment='Тест'
            )

    def test_view_reviews_for_service(self):
        """Тест: view_reviews() показва ревютата за услуга."""
        # Arrange
        self.user.leave_review(
            service_id=self.service.id,
            rating=5,
            comment='Страхотно!'
        )

        # Втори потребител оставя ревю
        user2 = RegisteredUser(username='user2', email='user2@test.com')
        user2.set_password('pass')
        db.session.add(user2)
        db.session.commit()
        user2.leave_review(
            service_id=self.service.id,
            rating=4,
            comment='Много добре'
        )

        # Act
        from models.user import Guest
        guest = Guest()
        result = guest.view_reviews(self.service.id)

        # Assert
        self.assertEqual(len(result), 2)


if __name__ == '__main__':
    unittest.main()
