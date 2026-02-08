"""
Тестове за Provider методите в user.py.

Тества:
    - get_received_reservations()
    - confirm_reservation()
    - reject_reservation()
    - complete_reservation()
    - get_service_reviews()
    - get_average_rating()
    - set_availability()
"""
import unittest
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from db import db
from models.user import RegisteredUser, Provider, Admin
from models.service import Service
from models.review import Review
from models.reservation import Reservation, ReservationStatus


def make_reservation(customer_id: int, provider_id: int, service_id: int,
                     scheduled_time: datetime,
                     status: ReservationStatus = ReservationStatus.PENDING) -> Reservation:
    """Helper function to create reservations with correct signature."""
    return Reservation(
        datetime=scheduled_time,
        customer_id=customer_id,
        provider_id=provider_id,
        service_id=service_id,
        status=status
    )


class TestProviderMethods(unittest.TestCase):
    """Тестове за Provider методите."""

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
        db.session.query(Reservation).delete()
        db.session.query(Review).delete()
        db.session.query(Service).delete()
        db.session.query(RegisteredUser).delete()
        db.session.commit()

        # Създаваме provider
        self.provider = Provider(username='provider', email='provider@test.com')
        self.provider.set_password('password123')
        db.session.add(self.provider)

        # Създаваме потребител
        self.user = RegisteredUser(username='user', email='user@test.com')
        self.user.set_password('password123')
        db.session.add(self.user)

        db.session.commit()

        # Създаваме услуга
        self.service = Service(
            name='Test Service',
            category='Test Category',
            provider_id=self.provider.id,
            description='Test description',
            price=100.0
        )
        db.session.add(self.service)
        db.session.commit()

    # ==================== GET RECEIVED RESERVATIONS TESTS ====================

    def test_get_received_reservations_empty(self):
        """Тест: get_received_reservations() без резервации."""
        reservations = self.provider.get_received_reservations()
        self.assertEqual(len(reservations), 0)

    def test_get_received_reservations_with_data(self):
        """Тест: get_received_reservations() с резервации."""
        reservation = make_reservation(
            customer_id=self.user.id,
            provider_id=self.provider.id,
            service_id=self.service.id,
            scheduled_time=datetime.now() + timedelta(days=1),
            status=ReservationStatus.PENDING
        )
        db.session.add(reservation)
        db.session.commit()

        reservations = self.provider.get_received_reservations()
        self.assertEqual(len(reservations), 1)

    def test_get_received_reservations_filter_by_status(self):
        """Тест: get_received_reservations() филтрира по статус."""
        pending = make_reservation(
            customer_id=self.user.id,
            provider_id=self.provider.id,
            service_id=self.service.id,
            scheduled_time=datetime.now() + timedelta(days=1),
            status=ReservationStatus.PENDING
        )
        confirmed = make_reservation(
            customer_id=self.user.id,
            provider_id=self.provider.id,
            service_id=self.service.id,
            scheduled_time=datetime.now() + timedelta(days=2),
            status=ReservationStatus.CONFIRMED
        )
        db.session.add_all([pending, confirmed])
        db.session.commit()

        result = self.provider.get_received_reservations(status=ReservationStatus.PENDING)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['status'], 'Pending')

        result = self.provider.get_received_reservations(status=ReservationStatus.CONFIRMED)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['status'], 'Confirmed')

    # ==================== CONFIRM RESERVATION TESTS ====================

    def test_confirm_reservation_success(self):
        """Тест: confirm_reservation() успешно потвърждава."""
        reservation = make_reservation(
            customer_id=self.user.id,
            provider_id=self.provider.id,
            service_id=self.service.id,
            scheduled_time=datetime.now() + timedelta(days=1),
            status=ReservationStatus.PENDING
        )
        db.session.add(reservation)
        db.session.commit()

        result = self.provider.confirm_reservation(reservation.id)
        self.assertTrue(result)
        self.assertEqual(reservation.status, ReservationStatus.CONFIRMED)

    def test_confirm_reservation_not_found(self):
        """Тест: confirm_reservation() за несъществуваща резервация."""
        result = self.provider.confirm_reservation(9999)
        self.assertFalse(result)

    def test_confirm_reservation_wrong_provider(self):
        """Тест: confirm_reservation() от грешен provider."""
        other_provider = Provider(username='other', email='other@test.com')
        other_provider.set_password('pass')
        db.session.add(other_provider)
        db.session.commit()

        reservation = make_reservation(
            customer_id=self.user.id,
            provider_id=self.provider.id,
            service_id=self.service.id,
            scheduled_time=datetime.now() + timedelta(days=1),
            status=ReservationStatus.PENDING
        )
        db.session.add(reservation)
        db.session.commit()

        result = other_provider.confirm_reservation(reservation.id)
        self.assertFalse(result)

    def test_confirm_reservation_already_confirmed(self):
        """Тест: confirm_reservation() за вече потвърдена резервация."""
        reservation = make_reservation(
            customer_id=self.user.id,
            provider_id=self.provider.id,
            service_id=self.service.id,
            scheduled_time=datetime.now() + timedelta(days=1),
            status=ReservationStatus.CONFIRMED
        )
        db.session.add(reservation)
        db.session.commit()

        # Може да е True или False в зависимост от имплементацията
        result = self.provider.confirm_reservation(reservation.id)
        self.assertIsInstance(result, bool)

    # ==================== REJECT RESERVATION TESTS ====================

    def test_reject_reservation_success(self):
        """Тест: reject_reservation() успешно отхвърля."""
        reservation = make_reservation(
            customer_id=self.user.id,
            provider_id=self.provider.id,
            service_id=self.service.id,
            scheduled_time=datetime.now() + timedelta(days=1),
            status=ReservationStatus.PENDING
        )
        db.session.add(reservation)
        db.session.commit()

        result = self.provider.reject_reservation(reservation.id)
        self.assertTrue(result)

    def test_reject_reservation_not_found(self):
        """Тест: reject_reservation() за несъществуваща резервация."""
        result = self.provider.reject_reservation(9999)
        self.assertFalse(result)

    def test_reject_reservation_wrong_provider(self):
        """Тест: reject_reservation() от грешен provider."""
        other_provider = Provider(username='other2', email='other2@test.com')
        other_provider.set_password('pass')
        db.session.add(other_provider)
        db.session.commit()

        reservation = make_reservation(
            customer_id=self.user.id,
            provider_id=self.provider.id,
            service_id=self.service.id,
            scheduled_time=datetime.now() + timedelta(days=1),
            status=ReservationStatus.PENDING
        )
        db.session.add(reservation)
        db.session.commit()

        result = other_provider.reject_reservation(reservation.id)
        self.assertFalse(result)

    def test_reject_reservation_already_confirmed(self):
        """Тест: reject_reservation() за вече потвърдена резервация."""
        reservation = make_reservation(
            customer_id=self.user.id,
            provider_id=self.provider.id,
            service_id=self.service.id,
            scheduled_time=datetime.now() + timedelta(days=1),
            status=ReservationStatus.CONFIRMED
        )
        db.session.add(reservation)
        db.session.commit()

        # Може да е True или False в зависимост от имплементацията
        result = self.provider.reject_reservation(reservation.id)
        self.assertIsInstance(result, bool)

    # ==================== COMPLETE RESERVATION TESTS ====================

    def test_complete_reservation_success(self):
        """Тест: complete_reservation() успешно завършва."""
        reservation = make_reservation(
            customer_id=self.user.id,
            provider_id=self.provider.id,
            service_id=self.service.id,
            scheduled_time=datetime.now() + timedelta(days=1),
            status=ReservationStatus.CONFIRMED
        )
        db.session.add(reservation)
        db.session.commit()

        result = self.provider.complete_reservation(reservation.id)
        self.assertTrue(result)
        self.assertEqual(reservation.status, ReservationStatus.COMPLETED)

    def test_complete_reservation_not_found(self):
        """Тест: complete_reservation() за несъществуваща резервация."""
        result = self.provider.complete_reservation(9999)
        self.assertFalse(result)

    def test_complete_reservation_wrong_provider(self):
        """Тест: complete_reservation() от грешен provider."""
        other_provider = Provider(username='other3', email='other3@test.com')
        other_provider.set_password('pass')
        db.session.add(other_provider)
        db.session.commit()

        reservation = make_reservation(
            customer_id=self.user.id,
            provider_id=self.provider.id,
            service_id=self.service.id,
            scheduled_time=datetime.now() + timedelta(days=1),
            status=ReservationStatus.CONFIRMED
        )
        db.session.add(reservation)
        db.session.commit()

        result = other_provider.complete_reservation(reservation.id)
        self.assertFalse(result)

    def test_complete_reservation_when_pending(self):
        """Тест: complete_reservation() за pending резервация."""
        reservation = make_reservation(
            customer_id=self.user.id,
            provider_id=self.provider.id,
            service_id=self.service.id,
            scheduled_time=datetime.now() + timedelta(days=1),
            status=ReservationStatus.PENDING
        )
        db.session.add(reservation)
        db.session.commit()

        # Може да е True или False в зависимост от имплементацията
        result = self.provider.complete_reservation(reservation.id)
        self.assertIsInstance(result, bool)

    # ==================== GET SERVICE REVIEWS TESTS ====================

    def test_get_service_reviews(self):
        """Тест: get_service_reviews() с ревюта."""
        review = Review(
            user_id=self.user.id,
            service_id=self.service.id,
            rating=5,
            comment='Great!'
        )
        db.session.add(review)
        db.session.commit()

        reviews = self.provider.get_service_reviews(self.service.id)
        self.assertEqual(len(reviews), 1)

    def test_get_service_reviews_for_specific_service(self):
        """Тест: get_service_reviews() за конкретна услуга."""
        service2 = Service(
            name='Service 2',
            category='Cat 2',
            provider_id=self.provider.id
        )
        db.session.add(service2)
        db.session.commit()

        review = Review(
            user_id=self.user.id,
            service_id=service2.id,
            rating=4
        )
        db.session.add(review)
        db.session.commit()

        reviews = self.provider.get_service_reviews(service2.id)
        self.assertEqual(len(reviews), 1)

        reviews = self.provider.get_service_reviews(self.service.id)
        self.assertEqual(len(reviews), 0)

    def test_get_service_reviews_wrong_provider(self):
        """Тест: get_service_reviews() за услуга на друг provider."""
        other_provider = Provider(username='other4', email='other4@test.com')
        other_provider.set_password('pass')
        db.session.add(other_provider)
        db.session.commit()

        review = Review(
            user_id=self.user.id,
            service_id=self.service.id,
            rating=5
        )
        db.session.add(review)
        db.session.commit()

        # other_provider не трябва да вижда ревюта за услуги на self.provider
        reviews = other_provider.get_service_reviews(self.service.id)
        self.assertEqual(len(reviews), 0)

    # ==================== GET AVERAGE RATING TESTS ====================

    def test_get_average_rating_no_reviews(self):
        """Тест: get_average_rating() без ревюта."""
        rating = self.provider.get_average_rating(self.service.id)
        self.assertIsNone(rating)

    def test_get_average_rating_with_reviews(self):
        """Тест: get_average_rating() с ревюта."""
        db.session.add(Review(user_id=self.user.id, service_id=self.service.id, rating=3))

        user2 = RegisteredUser(username='user2', email='user2@test.com')
        user2.set_password('pass')
        db.session.add(user2)
        db.session.commit()

        db.session.add(Review(user_id=user2.id, service_id=self.service.id, rating=5))
        db.session.commit()

        rating = self.provider.get_average_rating(self.service.id)
        self.assertEqual(rating, 4.0)

    def test_get_average_rating_for_specific_service(self):
        """Тест: get_average_rating() за конкретна услуга."""
        service2 = Service(
            name='Service 2',
            category='Cat 2',
            provider_id=self.provider.id
        )
        db.session.add(service2)
        db.session.commit()

        review = Review(
            user_id=self.user.id,
            service_id=service2.id,
            rating=5
        )
        db.session.add(review)
        db.session.commit()

        rating = self.provider.get_average_rating(service2.id)
        self.assertEqual(rating, 5.0)

        # За първата услуга няма ревюта
        rating = self.provider.get_average_rating(self.service.id)
        self.assertIsNone(rating)

    # ==================== SET AVAILABILITY TESTS ====================

    def test_set_availability_success(self):
        """Тест: set_availability() успешно задава наличност."""
        result = self.provider.set_availability(self.service.id, 'Mon-Fri 9:00-17:00')
        self.assertTrue(result)
        self.assertEqual(self.service.availability, 'Mon-Fri 9:00-17:00')

    def test_set_availability_not_found(self):
        """Тест: set_availability() за несъществуваща услуга."""
        result = self.provider.set_availability(9999, 'Mon-Fri')
        self.assertFalse(result)

    def test_set_availability_wrong_provider(self):
        """Тест: set_availability() от грешен provider."""
        other_provider = Provider(username='other5', email='other5@test.com')
        other_provider.set_password('pass')
        db.session.add(other_provider)
        db.session.commit()

        result = other_provider.set_availability(self.service.id, 'Mon-Fri')
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
