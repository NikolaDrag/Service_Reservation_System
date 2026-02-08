"""
Тестове за Favorites и Notifications функционалности.

Тества:
    - RegisteredUser методи за favorites
    - RegisteredUser методи за notifications
    - Routes за favorites
    - Routes за notifications
"""
import unittest
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from db import db
from models.user import RegisteredUser, Provider, UserRole
from models.service import Service
from models.favorite import Favorite
from models.notification import Notification, NotificationType


class TestFavoriteMethods(unittest.TestCase):
    """Тестове за методите на RegisteredUser за любими услуги."""

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
        db.session.query(Favorite).delete()
        db.session.query(Service).delete()
        db.session.query(RegisteredUser).delete()
        db.session.commit()

        # Създаваме потребител
        self.user = RegisteredUser(username='testuser', email='test@test.com')
        self.user.set_password('password123')
        db.session.add(self.user)

        # Създаваме provider
        self.provider = Provider(username='provider', email='provider@test.com')
        self.provider.set_password('password123')
        db.session.add(self.provider)
        db.session.commit()

        # Създаваме услуга
        self.service = Service(
            name='Test Service',
            category='Test',
            provider_id=self.provider.id
        )
        db.session.add(self.service)
        db.session.commit()

    def test_add_favorite_success(self):
        """Тест: add_favorite() добавя услуга към любими."""
        result = self.user.add_favorite(self.service.id)
        self.assertTrue(result)

        favorites = self.user.get_favorites()
        self.assertEqual(len(favorites), 1)
        self.assertEqual(favorites[0]['service_id'], self.service.id)

    def test_add_favorite_duplicate(self):
        """Тест: add_favorite() връща False при дубликат."""
        self.user.add_favorite(self.service.id)
        result = self.user.add_favorite(self.service.id)
        self.assertFalse(result)

    def test_add_favorite_nonexistent_service(self):
        """Тест: add_favorite() хвърля ValueError за несъществуваща услуга."""
        with self.assertRaises(ValueError):
            self.user.add_favorite(9999)

    def test_remove_favorite_success(self):
        """Тест: remove_favorite() премахва от любими."""
        self.user.add_favorite(self.service.id)
        result = self.user.remove_favorite(self.service.id)
        self.assertTrue(result)

        favorites = self.user.get_favorites()
        self.assertEqual(len(favorites), 0)

    def test_remove_favorite_not_exists(self):
        """Тест: remove_favorite() връща False ако не е в любими."""
        result = self.user.remove_favorite(self.service.id)
        self.assertFalse(result)

    def test_get_favorites_empty(self):
        """Тест: get_favorites() връща празен списък."""
        favorites = self.user.get_favorites()
        self.assertEqual(len(favorites), 0)

    def test_get_favorites_multiple(self):
        """Тест: get_favorites() връща всички любими."""
        service2 = Service(
            name='Service 2',
            category='Test',
            provider_id=self.provider.id
        )
        db.session.add(service2)
        db.session.commit()

        self.user.add_favorite(self.service.id)
        self.user.add_favorite(service2.id)

        favorites = self.user.get_favorites()
        self.assertEqual(len(favorites), 2)


class TestNotificationMethods(unittest.TestCase):
    """Тестове за методите на RegisteredUser за известия."""

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
        db.session.query(Notification).delete()
        db.session.query(RegisteredUser).delete()
        db.session.commit()

        self.user = RegisteredUser(username='testuser', email='test@test.com')
        self.user.set_password('password123')
        db.session.add(self.user)
        db.session.commit()

    def test_get_notifications_empty(self):
        """Тест: get_notifications() връща празен списък."""
        result = self.user.get_notifications()
        self.assertEqual(len(result['notifications']), 0)
        self.assertEqual(result['unread_count'], 0)

    def test_get_notifications_with_data(self):
        """Тест: get_notifications() връща известията."""
        notification = Notification(
            user_id=self.user.id,
            message='Тестово известие',
            notification_type=NotificationType.RESERVATION_CONFIRMED
        )
        db.session.add(notification)
        db.session.commit()

        result = self.user.get_notifications()
        self.assertEqual(len(result['notifications']), 1)
        self.assertEqual(result['unread_count'], 1)

    def test_get_notifications_unread_only(self):
        """Тест: get_notifications(unread_only=True) филтрира."""
        # Прочетено известие
        notification1 = Notification(
            user_id=self.user.id,
            message='Прочетено',
            notification_type=NotificationType.RESERVATION_CONFIRMED
        )
        notification1.is_read = True

        # Непрочетено известие
        notification2 = Notification(
            user_id=self.user.id,
            message='Непрочетено',
            notification_type=NotificationType.RESERVATION_CANCELLED
        )

        db.session.add_all([notification1, notification2])
        db.session.commit()

        result = self.user.get_notifications(unread_only=True)
        self.assertEqual(len(result['notifications']), 1)
        self.assertEqual(result['notifications'][0]['message'], 'Непрочетено')

    def test_mark_notification_read_success(self):
        """Тест: mark_notification_read() маркира като прочетено."""
        notification = Notification(
            user_id=self.user.id,
            message='Тестово',
            notification_type=NotificationType.RESERVATION_CONFIRMED
        )
        db.session.add(notification)
        db.session.commit()

        result = self.user.mark_notification_read(notification.id)
        self.assertTrue(result)

        # Проверяваме че е прочетено
        updated = db.session.get(Notification, notification.id)
        assert updated is not None
        self.assertTrue(updated.is_read)

    def test_mark_notification_read_not_found(self):
        """Тест: mark_notification_read() връща False за несъществуващо."""
        result = self.user.mark_notification_read(9999)
        self.assertFalse(result)

    def test_mark_notification_read_wrong_user(self):
        """Тест: mark_notification_read() връща False за чуждо известие."""
        other_user = RegisteredUser(username='other', email='other@test.com')
        other_user.set_password('pass')
        db.session.add(other_user)
        db.session.commit()

        notification = Notification(
            user_id=other_user.id,
            message='Чуждо известие',
            notification_type=NotificationType.RESERVATION_CONFIRMED
        )
        db.session.add(notification)
        db.session.commit()

        result = self.user.mark_notification_read(notification.id)
        self.assertFalse(result)

    def test_mark_all_notifications_read(self):
        """Тест: mark_all_notifications_read() маркира всички."""
        for i in range(3):
            notification = Notification(
                user_id=self.user.id,
                message=f'Известие {i}',
                notification_type=NotificationType.RESERVATION_CONFIRMED
            )
            db.session.add(notification)
        db.session.commit()

        count = self.user.mark_all_notifications_read()
        self.assertEqual(count, 3)

        result = self.user.get_notifications()
        self.assertEqual(result['unread_count'], 0)


class TestFavoriteRoutes(unittest.TestCase):
    """Тестове за favorites routes."""

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
        db.session.query(Favorite).delete()
        db.session.query(Service).delete()
        db.session.query(RegisteredUser).delete()
        db.session.commit()

        self.user = RegisteredUser(username='testuser', email='test@test.com')
        self.user.set_password('password123')
        db.session.add(self.user)

        self.provider = Provider(username='provider', email='provider@test.com')
        self.provider.set_password('password123')
        db.session.add(self.provider)
        db.session.commit()

        self.service = Service(
            name='Test Service',
            category='Test',
            provider_id=self.provider.id
        )
        db.session.add(self.service)
        db.session.commit()

    def test_get_favorites_unauthorized(self):
        """Тест: GET /favorites без auth връща 401."""
        response = self.client.get('/api/favorites')
        self.assertEqual(response.status_code, 401)

    def test_get_favorites_success(self):
        """Тест: GET /favorites връща любимите."""
        response = self.client.get(
            '/api/favorites',
            headers={'X-User-ID': str(self.user.id)}
        )
        self.assertEqual(response.status_code, 200)

    def test_add_favorite_success(self):
        """Тест: POST /favorites добавя любима."""
        response = self.client.post(
            '/api/favorites',
            headers={'X-User-ID': str(self.user.id)},
            json={'service_id': self.service.id}
        )
        self.assertEqual(response.status_code, 201)

    def test_add_favorite_missing_service_id(self):
        """Тест: POST /favorites без service_id връща 400."""
        response = self.client.post(
            '/api/favorites',
            headers={'X-User-ID': str(self.user.id)},
            json={}
        )
        self.assertEqual(response.status_code, 400)

    def test_add_favorite_duplicate(self):
        """Тест: POST /favorites дубликат връща 400."""
        self.client.post(
            '/api/favorites',
            headers={'X-User-ID': str(self.user.id)},
            json={'service_id': self.service.id}
        )
        response = self.client.post(
            '/api/favorites',
            headers={'X-User-ID': str(self.user.id)},
            json={'service_id': self.service.id}
        )
        self.assertEqual(response.status_code, 400)

    def test_add_favorite_nonexistent_service(self):
        """Тест: POST /favorites за несъществуваща услуга връща 404."""
        response = self.client.post(
            '/api/favorites',
            headers={'X-User-ID': str(self.user.id)},
            json={'service_id': 9999}
        )
        self.assertEqual(response.status_code, 404)

    def test_remove_favorite_success(self):
        """Тест: DELETE /favorites/:id премахва."""
        self.user.add_favorite(self.service.id)

        response = self.client.delete(
            f'/api/favorites/{self.service.id}',
            headers={'X-User-ID': str(self.user.id)}
        )
        self.assertEqual(response.status_code, 200)

    def test_remove_favorite_not_found(self):
        """Тест: DELETE /favorites/:id за несъществуващ връща 404."""
        response = self.client.delete(
            f'/api/favorites/{self.service.id}',
            headers={'X-User-ID': str(self.user.id)}
        )
        self.assertEqual(response.status_code, 404)


class TestNotificationRoutes(unittest.TestCase):
    """Тестове за notifications routes."""

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
        db.session.query(Notification).delete()
        db.session.query(RegisteredUser).delete()
        db.session.commit()

        self.user = RegisteredUser(username='testuser', email='test@test.com')
        self.user.set_password('password123')
        db.session.add(self.user)
        db.session.commit()

    def test_get_notifications_unauthorized(self):
        """Тест: GET /notifications без auth връща 401."""
        response = self.client.get('/api/notifications')
        self.assertEqual(response.status_code, 401)

    def test_get_notifications_success(self):
        """Тест: GET /notifications връща известията."""
        response = self.client.get(
            '/api/notifications',
            headers={'X-User-ID': str(self.user.id)}
        )
        self.assertEqual(response.status_code, 200)

    def test_get_notifications_unread_only(self):
        """Тест: GET /notifications?unread_only=true филтрира."""
        response = self.client.get(
            '/api/notifications?unread_only=true',
            headers={'X-User-ID': str(self.user.id)}
        )
        self.assertEqual(response.status_code, 200)

    def test_mark_as_read_success(self):
        """Тест: PUT /notifications/:id/read маркира."""
        notification = Notification(
            user_id=self.user.id,
            message='Тест',
            notification_type=NotificationType.RESERVATION_CONFIRMED
        )
        db.session.add(notification)
        db.session.commit()

        response = self.client.put(
            f'/api/notifications/{notification.id}/read',
            headers={'X-User-ID': str(self.user.id)}
        )
        self.assertEqual(response.status_code, 200)

    def test_mark_as_read_not_found(self):
        """Тест: PUT /notifications/:id/read за несъществуващо връща 404."""
        response = self.client.put(
            '/api/notifications/9999/read',
            headers={'X-User-ID': str(self.user.id)}
        )
        self.assertEqual(response.status_code, 404)

    def test_mark_all_as_read_success(self):
        """Тест: PUT /notifications/read-all маркира всички."""
        for i in range(2):
            notification = Notification(
                user_id=self.user.id,
                message=f'Известие {i}',
                notification_type=NotificationType.RESERVATION_CONFIRMED
            )
            db.session.add(notification)
        db.session.commit()

        response = self.client.put(
            '/api/notifications/read-all',
            headers={'X-User-ID': str(self.user.id)}
        )
        self.assertEqual(response.status_code, 200)


class TestNotificationModel(unittest.TestCase):
    """Тестове за Notification модела."""

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
        db.session.query(Notification).delete()
        db.session.query(RegisteredUser).delete()
        db.session.commit()

        self.user = RegisteredUser(username='testuser', email='test@test.com')
        self.user.set_password('password123')
        db.session.add(self.user)
        db.session.commit()

    def test_notification_creation(self):
        """Тест: Създаване на известие."""
        notification = Notification(
            user_id=self.user.id,
            message='Резервацията е потвърдена',
            notification_type=NotificationType.RESERVATION_CONFIRMED,
            related_id=123
        )
        db.session.add(notification)
        db.session.commit()

        self.assertIsNotNone(notification.id)
        self.assertFalse(notification.is_read)
        self.assertEqual(notification.related_id, 123)

    def test_notification_mark_as_read(self):
        """Тест: mark_as_read() метод."""
        notification = Notification(
            user_id=self.user.id,
            message='Тест',
            notification_type=NotificationType.RESERVATION_CANCELLED
        )
        db.session.add(notification)
        db.session.commit()

        notification.mark_as_read()
        self.assertTrue(notification.is_read)

    def test_notification_to_dict(self):
        """Тест: to_dict() метод."""
        notification = Notification(
            user_id=self.user.id,
            message='Тест',
            notification_type=NotificationType.NEW_REVIEW
        )
        db.session.add(notification)
        db.session.commit()

        result = notification.to_dict()
        self.assertEqual(result['message'], 'Тест')
        self.assertEqual(result['type'], 'new_review')
        self.assertFalse(result['is_read'])


class TestFavoriteModel(unittest.TestCase):
    """Тестове за Favorite модела."""

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
        db.session.query(Favorite).delete()
        db.session.query(Service).delete()
        db.session.query(RegisteredUser).delete()
        db.session.commit()

        self.user = RegisteredUser(username='testuser', email='test@test.com')
        self.user.set_password('password123')
        db.session.add(self.user)

        self.provider = Provider(username='provider', email='provider@test.com')
        self.provider.set_password('password123')
        db.session.add(self.provider)
        db.session.commit()

        self.service = Service(
            name='Test Service',
            category='Test',
            provider_id=self.provider.id
        )
        db.session.add(self.service)
        db.session.commit()

    def test_favorite_creation(self):
        """Тест: Създаване на любима услуга."""
        favorite = Favorite(user_id=self.user.id, service_id=self.service.id)
        db.session.add(favorite)
        db.session.commit()

        self.assertIsNotNone(favorite.id)
        self.assertIsNotNone(favorite.created_at)

    def test_favorite_to_dict(self):
        """Тест: to_dict() метод."""
        favorite = Favorite(user_id=self.user.id, service_id=self.service.id)
        db.session.add(favorite)
        db.session.commit()

        result = favorite.to_dict()
        self.assertEqual(result['user_id'], self.user.id)
        self.assertEqual(result['service_id'], self.service.id)
        self.assertIn('created_at', result)


if __name__ == '__main__':
    unittest.main()
