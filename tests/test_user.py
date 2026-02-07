"""
Тестове за класовете Guest, RegisteredUser, Provider, Admin.

Структура (Arrange-Act-Assert):
    - Arrange: Подготовка на данни
    - Act: Изпълнение на тествания метод
    - Assert: Проверка на резултата
"""
import unittest
import sys
import os

# Добавяме родителската директория към sys.path
# за да можем да импортираме модулите
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from db import db
from models.user import Guest, RegisteredUser, Provider, Admin, UserRole
from models.service import Service
from models.reservation import Reservation, ReservationStatus
from models.review import Review


class TestGuest(unittest.TestCase):
    """Тестове за Guest класа."""

    @classmethod
    def setUpClass(cls):
        """
        Изпълнява се ВЕДНЪЖ преди всички тестове в класа.
        Създава тестова база данни.
        """
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True
        cls.app = app
        cls.app_context = app.app_context()
        cls.app_context.push()
        db.create_all()

    @classmethod
    def tearDownClass(cls):
        """
        Изпълнява се ВЕДНЪЖ след всички тестове в класа.
        Изтрива тестовата база данни.
        """
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()

    def setUp(self):
        """Изпълнява се ПРЕДИ всеки тест."""
        # Изчистваме таблиците преди всеки тест
        db.session.query(Review).delete()
        db.session.query(Reservation).delete()
        db.session.query(Service).delete()
        db.session.query(RegisteredUser).delete()
        db.session.commit()

        # Създаваме тестови доставчик
        self.provider = Provider(
            username='test_provider',
            email='provider@test.com'
        )
        self.provider.set_password('password123')
        db.session.add(self.provider)
        db.session.commit()

        # Създаваме тестови услуги (английски имена за SQLite lower() съвместимост)
        self.service1 = Service(
            name='Haircut Service',
            category='Beauty',
            provider_id=self.provider.id,
            description='Professional haircut',
            price=25.0
        )
        self.service2 = Service(
            name='Massage',
            category='Spa',
            provider_id=self.provider.id,
            description='Relaxing massage',
            price=50.0
        )
        db.session.add(self.service1)
        db.session.add(self.service2)
        db.session.commit()

    def test_search_services_all(self):
        """Тест: search_services() без филтри връща всички услуги."""
        # Arrange
        guest = Guest()

        # Act
        result = guest.search_services()

        # Assert
        self.assertEqual(len(result), 2)

    def test_search_services_by_name(self):
        """Тест: search_services() филтрира по име."""
        # Arrange
        guest = Guest()

        # Act - търсим "massage" (case-insensitive)
        result = guest.search_services(name='massage')

        # Assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'Massage')

    def test_search_services_by_category(self):
        """Тест: search_services() филтрира по категория."""
        # Arrange
        guest = Guest()

        # Act - търсим "beauty" (case-insensitive)
        result = guest.search_services(category='beauty')

        # Assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'Haircut Service')

    def test_search_services_no_results(self):
        """Тест: search_services() връща празен списък ако няма съвпадения."""
        # Arrange
        guest = Guest()

        # Act
        result = guest.search_services(name='Несъществуваща услуга')

        # Assert
        self.assertEqual(len(result), 0)

    def test_view_service_existing(self):
        """Тест: view_service() връща услуга по ID."""
        # Arrange
        guest = Guest()

        # Act
        result = guest.view_service(self.service1.id)

        # Assert
        self.assertIsNotNone(result)
        assert result is not None  # type guard за Pylance
        self.assertEqual(result['name'], 'Haircut Service')

    def test_view_service_not_found(self):
        """Тест: view_service() връща None за несъществуващо ID."""
        # Arrange
        guest = Guest()

        # Act
        result = guest.view_service(9999)

        # Assert
        self.assertIsNone(result)

    def test_view_reviews_empty(self):
        """Тест: view_reviews() връща празен списък ако няма ревюта."""
        # Arrange
        guest = Guest()

        # Act
        result = guest.view_reviews(self.service1.id)

        # Assert
        self.assertEqual(len(result), 0)


class TestRegisteredUser(unittest.TestCase):
    """Тестове за RegisteredUser класа."""

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

    def test_create_user(self):
        """Тест: Създаване на потребител."""
        # Arrange & Act
        user = RegisteredUser(
            username='testuser',
            email='test@example.com'
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        # Assert
        self.assertIsNotNone(user.id)
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.role, UserRole.USER)

    def test_set_password_and_check(self):
        """Тест: set_password() хешира паролата, check_password() я проверява."""
        # Arrange
        user = RegisteredUser(
            username='testuser',
            email='test@example.com'
        )

        # Act
        user.set_password('mypassword')

        # Assert
        self.assertNotEqual(user.password_hash, 'mypassword')  # Не е plain text
        self.assertTrue(user.check_password('mypassword'))  # Правилна парола
        self.assertFalse(user.check_password('wrongpassword'))  # Грешна парола

    def test_login_with_email(self):
        """Тест: login() работи с имейл."""
        # Arrange
        user = RegisteredUser(username='testuser', email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        # Act
        result = RegisteredUser.login('test@example.com', 'password123')

        # Assert
        self.assertIsNotNone(result)
        assert result is not None  # type guard за Pylance
        self.assertEqual(result.username, 'testuser')

    def test_login_with_username(self):
        """Тест: login() работи с потребителско име."""
        # Arrange
        user = RegisteredUser(username='testuser', email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        # Act
        result = RegisteredUser.login('testuser', 'password123')

        # Assert
        self.assertIsNotNone(result)
        assert result is not None  # type guard за Pylance
        self.assertEqual(result.email, 'test@example.com')

    def test_login_wrong_password(self):
        """Тест: login() връща None при грешна парола."""
        # Arrange
        user = RegisteredUser(username='testuser', email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        # Act
        result = RegisteredUser.login('testuser', 'wrongpassword')

        # Assert
        self.assertIsNone(result)

    def test_login_nonexistent_user(self):
        """Тест: login() връща None за несъществуващ потребител."""
        # Act
        result = RegisteredUser.login('nouser', 'password123')

        # Assert
        self.assertIsNone(result)

    def test_to_dict(self):
        """Тест: to_dict() връща речник с данните."""
        # Arrange
        user = RegisteredUser(
            username='testuser',
            email='test@example.com',
            role=UserRole.PROVIDER
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        # Act
        result = user.to_dict()

        # Assert
        self.assertEqual(result['username'], 'testuser')
        self.assertEqual(result['email'], 'test@example.com')
        self.assertEqual(result['role'], 'provider')
        self.assertNotIn('password_hash', result)  # Не трябва да има парола!


class TestProvider(unittest.TestCase):
    """Тестове за Provider класа."""

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

        # Създаваме тестов доставчик
        self.provider = Provider(
            username='test_provider',
            email='provider@test.com'
        )
        self.provider.set_password('password123')
        db.session.add(self.provider)
        db.session.commit()

    def test_provider_inherits_from_registered_user(self):
        """Тест: Provider наследява RegisteredUser."""
        # Assert
        self.assertIsInstance(self.provider, RegisteredUser)
        self.assertIsInstance(self.provider, Guest)

    def test_provider_role(self):
        """Тест: Provider има роля PROVIDER."""
        # Assert
        self.assertEqual(self.provider.role, UserRole.PROVIDER)

    def test_create_service(self):
        """Тест: create_service() създава услуга."""
        # Act
        service = self.provider.create_service(
            name='Тестова услуга',
            description='Описание',
            category='Тест',
            price=100.0
        )

        # Assert
        self.assertIsNotNone(service)
        self.assertEqual(service.name, 'Тестова услуга')  # Обект, не речник
        self.assertEqual(service.provider_id, self.provider.id)

    def test_get_my_services(self):
        """Тест: get_my_services() връща само услугите на доставчика."""
        # Arrange
        self.provider.create_service(
            name='Услуга 1', description='Описание 1',
            category='Кат1', price=10.0
        )
        self.provider.create_service(
            name='Услуга 2', description='Описание 2',
            category='Кат2', price=20.0
        )

        # Друг доставчик - неговите услуги НЕ трябва да се виждат
        other_provider = Provider(username='other', email='other@test.com')
        other_provider.set_password('pass')
        db.session.add(other_provider)
        db.session.commit()
        other_provider.create_service(
            name='Чужда услуга', description='Чуждо',
            category='Друга', price=30.0
        )

        # Act
        result = self.provider.get_my_services()

        # Assert
        self.assertEqual(len(result), 2)

    def test_update_service(self):
        """Тест: update_service() променя услуга."""
        # Arrange
        service = self.provider.create_service(
            name='Стара', description='Стара услуга',
            category='Кат', price=10.0
        )
        service_id = service.id

        # Act
        result = self.provider.update_service(service_id, name='Нова', price=50.0)

        # Assert
        self.assertTrue(result)  # Връща bool
        # Проверяваме дали наистина е обновена
        updated = db.session.get(Service, service_id)
        assert updated is not None  # type guard за Pylance
        self.assertEqual(updated.name, 'Нова')
        self.assertEqual(updated.price, 50.0)

    def test_delete_service(self):
        """Тест: delete_service() изтрива услуга."""
        # Arrange
        service = self.provider.create_service(
            name='За изтриване', description='Тест',
            category='Кат', price=10.0
        )
        service_id = service.id

        # Act
        result = self.provider.delete_service(service_id)

        # Assert
        self.assertTrue(result)
        self.assertIsNone(db.session.get(Service, service_id))


class TestAdmin(unittest.TestCase):
    """Тестове за Admin класа."""

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

        # Създаваме тестов админ
        self.admin = Admin(
            username='test_admin',
            email='admin@test.com'
        )
        self.admin.set_password('admin123')
        db.session.add(self.admin)
        db.session.commit()

    def test_admin_inherits_from_provider(self):
        """Тест: Admin наследява Provider."""
        # Assert
        self.assertIsInstance(self.admin, Provider)
        self.assertIsInstance(self.admin, RegisteredUser)
        self.assertIsInstance(self.admin, Guest)

    def test_admin_role(self):
        """Тест: Admin има роля ADMIN."""
        # Assert
        self.assertEqual(self.admin.role, UserRole.ADMIN)

    def test_get_all_users(self):
        """Тест: get_all_users() връща всички потребители."""
        # Arrange
        user = RegisteredUser(username='user1', email='user1@test.com')
        user.set_password('pass')
        db.session.add(user)
        db.session.commit()

        # Act
        result = self.admin.get_all_users()

        # Assert
        self.assertEqual(len(result), 2)  # admin + user1

    def test_delete_user(self):
        """Тест: delete_user() изтрива потребител."""
        # Arrange
        user = RegisteredUser(username='to_delete', email='delete@test.com')
        user.set_password('pass')
        db.session.add(user)
        db.session.commit()
        user_id = user.id

        # Act
        result = self.admin.delete_user(user_id)

        # Assert
        self.assertTrue(result)
        self.assertIsNone(db.session.get(RegisteredUser, user_id))

    def test_change_user_role(self):
        """Тест: change_user_role() променя ролята на потребител."""
        # Arrange
        user = RegisteredUser(username='user1', email='user1@test.com')
        user.set_password('pass')
        db.session.add(user)
        db.session.commit()

        # Act - подаваме UserRole enum, не string
        result = self.admin.change_user_role(user.id, UserRole.PROVIDER)

        # Assert
        self.assertTrue(result)
        # Проверяваме дали ролята е променена
        updated_user = db.session.get(RegisteredUser, user.id)
        assert updated_user is not None  # type guard за Pylance
        self.assertEqual(updated_user.role, UserRole.PROVIDER)

    def test_get_statistics(self):
        """Тест: get_statistics() връща статистика."""
        # Act
        result = self.admin.get_statistics()

        # Assert
        self.assertIn('total_users', result)
        self.assertIn('total_services', result)
        self.assertIn('total_reservations', result)
        self.assertIn('total_reviews', result)


if __name__ == '__main__':
    # Изпълнява тестовете когато файлът се стартира директно
    unittest.main()
