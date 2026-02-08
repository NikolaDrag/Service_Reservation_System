"""
Тестове за Admin методите в user.py.

Тества:
    - get_all_users()
    - delete_user()
    - change_user_role()
    - get_all_services()
    - delete_any_service()
    - get_all_reservations()
    - delete_reservation()
    - Category management
    - get_statistics()
    - create_initial_admin()
"""
import unittest
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from db import db
from models.user import RegisteredUser, Provider, Admin, UserRole
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


class TestAdminMethods(unittest.TestCase):
    """Тестове за Admin методите."""

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

        # Създаваме admin
        self.admin = Admin(username='admin', email='admin@test.com')
        self.admin.set_password('admin123')
        db.session.add(self.admin)

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

    # ==================== GET ALL USERS TESTS ====================

    def test_get_all_users(self):
        """Тест: get_all_users() връща всички потребители."""
        users = self.admin.get_all_users()
        self.assertEqual(len(users), 3)  # admin, provider, user

    def test_get_all_users_filter_by_role(self):
        """Тест: get_all_users() филтрира по роля."""
        providers = self.admin.get_all_users(role=UserRole.PROVIDER)
        self.assertEqual(len(providers), 1)
        self.assertEqual(providers[0]['username'], 'provider')

        admins = self.admin.get_all_users(role=UserRole.ADMIN)
        self.assertEqual(len(admins), 1)
        self.assertEqual(admins[0]['username'], 'admin')

    # ==================== DELETE USER TESTS ====================

    def test_delete_user_success(self):
        """Тест: delete_user() успешно изтрива потребител."""
        user_id = self.user.id
        result = self.admin.delete_user(user_id)
        self.assertTrue(result)

        deleted = db.session.get(RegisteredUser, user_id)
        self.assertIsNone(deleted)

    def test_delete_user_not_found(self):
        """Тест: delete_user() за несъществуващ потребител."""
        result = self.admin.delete_user(9999)
        self.assertFalse(result)

    def test_delete_user_cannot_delete_self(self):
        """Тест: delete_user() не може да изтрие себе си."""
        result = self.admin.delete_user(self.admin.id)
        self.assertFalse(result)

    # ==================== CHANGE USER ROLE TESTS ====================

    def test_change_user_role_to_provider(self):
        """Тест: change_user_role() променя роля на provider."""
        result = self.admin.change_user_role(self.user.id, UserRole.PROVIDER)
        self.assertTrue(result)

        updated = db.session.get(RegisteredUser, self.user.id)
        assert updated is not None
        self.assertEqual(updated.role, UserRole.PROVIDER)

    def test_change_user_role_to_admin(self):
        """Тест: change_user_role() променя роля на admin."""
        result = self.admin.change_user_role(self.user.id, UserRole.ADMIN)
        self.assertTrue(result)

        updated = db.session.get(RegisteredUser, self.user.id)
        assert updated is not None
        self.assertEqual(updated.role, UserRole.ADMIN)

    def test_change_user_role_not_found(self):
        """Тест: change_user_role() за несъществуващ потребител."""
        result = self.admin.change_user_role(9999, UserRole.PROVIDER)
        self.assertFalse(result)

    def test_change_user_role_cannot_change_self(self):
        """Тест: change_user_role() не може да промени собствената си роля."""
        result = self.admin.change_user_role(self.admin.id, UserRole.USER)
        self.assertFalse(result)

    # ==================== GET ALL SERVICES TESTS ====================

    def test_get_all_services(self):
        """Тест: get_all_services() връща всички услуги."""
        services = self.admin.get_all_services()
        self.assertEqual(len(services), 1)

    def test_get_all_services_filter_by_category(self):
        """Тест: get_all_services() филтрира по категория."""
        service2 = Service(
            name='Service 2',
            category='Other Category',
            provider_id=self.provider.id
        )
        db.session.add(service2)
        db.session.commit()

        test_services = self.admin.get_all_services(category='Test Category')
        self.assertEqual(len(test_services), 1)

        other_services = self.admin.get_all_services(category='Other Category')
        self.assertEqual(len(other_services), 1)

    # ==================== DELETE ANY SERVICE TESTS ====================

    def test_delete_any_service_success(self):
        """Тест: delete_any_service() успешно изтрива услуга."""
        service_id = self.service.id
        result = self.admin.delete_any_service(service_id)
        self.assertTrue(result)

        deleted = db.session.get(Service, service_id)
        self.assertIsNone(deleted)

    def test_delete_any_service_not_found(self):
        """Тест: delete_any_service() за несъществуваща услуга."""
        result = self.admin.delete_any_service(9999)
        self.assertFalse(result)

    # ==================== GET ALL RESERVATIONS TESTS ====================

    def test_get_all_reservations(self):
        """Тест: get_all_reservations() връща всички резервации."""
        reservation = make_reservation(
            customer_id=self.user.id,
            provider_id=self.provider.id,
            service_id=self.service.id,
            scheduled_time=datetime.now() + timedelta(days=1),
            status=ReservationStatus.PENDING
        )
        db.session.add(reservation)
        db.session.commit()

        reservations = self.admin.get_all_reservations()
        self.assertEqual(len(reservations), 1)

    def test_get_all_reservations_filter_by_status(self):
        """Тест: get_all_reservations() филтрира по статус."""
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

        pending_only = self.admin.get_all_reservations(status=ReservationStatus.PENDING)
        self.assertEqual(len(pending_only), 1)

    # ==================== DELETE RESERVATION TESTS ====================

    def test_delete_reservation_success(self):
        """Тест: delete_reservation() успешно изтрива."""
        reservation = make_reservation(
            customer_id=self.user.id,
            provider_id=self.provider.id,
            service_id=self.service.id,
            scheduled_time=datetime.now() + timedelta(days=1),
            status=ReservationStatus.PENDING
        )
        db.session.add(reservation)
        db.session.commit()

        result = self.admin.delete_reservation(reservation.id)
        self.assertTrue(result)

        deleted = db.session.get(Reservation, reservation.id)
        self.assertIsNone(deleted)

    def test_delete_reservation_not_found(self):
        """Тест: delete_reservation() за несъществуваща резервация."""
        result = self.admin.delete_reservation(9999)
        self.assertFalse(result)

    # ==================== CATEGORY MANAGEMENT TESTS ====================

    def test_get_all_categories(self):
        """Тест: get_all_categories() връща всички категории."""
        service2 = Service(
            name='Service 2',
            category='Other Category',
            provider_id=self.provider.id
        )
        db.session.add(service2)
        db.session.commit()

        categories = self.admin.get_all_categories()
        self.assertEqual(len(categories), 2)
        self.assertIn('Test Category', categories)
        self.assertIn('Other Category', categories)

    def test_rename_category_success(self):
        """Тест: rename_category() успешно преименува."""
        result = self.admin.rename_category('Test Category', 'New Category')
        self.assertTrue(result)

        # Проверяваме че услугата има новата категория
        updated = db.session.get(Service, self.service.id)
        assert updated is not None
        self.assertEqual(updated.category, 'New Category')

    def test_rename_category_not_found(self):
        """Тест: rename_category() за несъществуваща категория."""
        result = self.admin.rename_category('NonExistent', 'New Name')
        self.assertFalse(result)

    def test_delete_category_success(self):
        """Тест: delete_category() успешно изтрива категория и услугите в нея."""
        service_id = self.service.id
        result = self.admin.delete_category('Test Category')
        self.assertTrue(result)

        # Услугата трябва да е изтрита
        deleted = db.session.get(Service, service_id)
        self.assertIsNone(deleted)

    def test_delete_category_not_found(self):
        """Тест: delete_category() за несъществуваща категория."""
        result = self.admin.delete_category('NonExistent')
        self.assertFalse(result)

    # ==================== GET STATISTICS TESTS ====================

    def test_get_statistics(self):
        """Тест: get_statistics() връща статистика."""
        # Добавяме резервация
        reservation = make_reservation(
            customer_id=self.user.id,
            provider_id=self.provider.id,
            service_id=self.service.id,
            scheduled_time=datetime.now() + timedelta(days=1),
            status=ReservationStatus.PENDING
        )
        db.session.add(reservation)

        # Добавяме ревю
        review = Review(
            user_id=self.user.id,
            service_id=self.service.id,
            rating=5
        )
        db.session.add(review)
        db.session.commit()

        stats = self.admin.get_statistics()

        # Проверяваме че статистиката съдържа всички ключове
        self.assertIn('total_users', stats)
        self.assertIn('total_services', stats)
        self.assertIn('total_reservations', stats)
        self.assertIn('total_reviews', stats)
        
        # Проверяваме че стойностите са >0
        self.assertGreaterEqual(stats['total_users'], 1)
        self.assertGreaterEqual(stats['total_services'], 1)
        self.assertGreaterEqual(stats['total_reservations'], 1)
        self.assertGreaterEqual(stats['total_reviews'], 1)


class TestAdminReservationRoutes(unittest.TestCase):
    """Тестове за admin reservation routes."""

    @classmethod
    def setUpClass(cls):
        """Създава тестова база данни."""
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True
        cls.app = app
        cls.client = app.test_client()
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

        self.admin = Admin(username='admin', email='admin@test.com')
        self.admin.set_password('admin123')
        db.session.add(self.admin)

        self.provider = Provider(username='provider', email='provider@test.com')
        self.provider.set_password('password123')
        db.session.add(self.provider)

        self.user = RegisteredUser(username='user', email='user@test.com')
        self.user.set_password('password123')
        db.session.add(self.user)

        db.session.commit()

        self.service = Service(
            name='Test Service',
            category='Test Category',
            provider_id=self.provider.id
        )
        db.session.add(self.service)
        db.session.commit()

    def test_admin_get_all_reservations(self):
        """Тест: GET /reservations от admin."""
        reservation = make_reservation(
            customer_id=self.user.id,
            provider_id=self.provider.id,
            service_id=self.service.id,
            scheduled_time=datetime.now() + timedelta(days=1),
            status=ReservationStatus.PENDING
        )
        db.session.add(reservation)
        db.session.commit()

        response = self.client.get(
            '/api/reservations',
            headers={'X-User-ID': str(self.admin.id)}
        )
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
