"""
Тестове за Notifications (известия).
"""
import pytest
from main import app
from db import db
from models.user import RegisteredUser
from models.notification import Notification, NotificationType


@pytest.fixture
def client():
    """Създава тестов клиент."""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.test_client() as test_client:
        with app.app_context():
            db.create_all()
            yield test_client
            db.session.remove()
            db.drop_all()


@pytest.fixture
def sample_user(client):
    """Създава примерен потребител."""
    with app.app_context():
        user = RegisteredUser(username='testuser', email='test@test.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        return user.id


@pytest.fixture
def sample_notifications(sample_user):
    """Създава примерни известия."""
    with app.app_context():
        # Създаваме 3 известия
        n1 = Notification(
            user_id=sample_user,
            title='Нова резервация',
            message='Имате нова резервация за смяна на масло',
            notification_type=NotificationType.RESERVATION_NEW
        )
        n2 = Notification(
            user_id=sample_user,
            title='Потвърдена резервация',
            message='Вашата резервация е потвърдена',
            notification_type=NotificationType.RESERVATION_CONFIRMED
        )
        n3 = Notification(
            user_id=sample_user,
            title='Системно съобщение',
            message='Добре дошли в системата!',
            notification_type=NotificationType.SYSTEM
        )
        n3.is_read = True  # Едно е прочетено

        db.session.add_all([n1, n2, n3])
        db.session.commit()

        return [n1.id, n2.id, n3.id]


class TestNotification:
    """Тестове за модела Notification."""

    def test_get_notifications(self, client, sample_user, sample_notifications):
        """Тест за получаване на известия."""
        response = client.get(
            '/api/notifications',
            headers={'X-User-ID': str(sample_user)}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert 'notifications' in data
        assert len(data['notifications']) == 3
        assert 'unread_count' in data
        assert data['unread_count'] == 2  # 2 непрочетени

    def test_get_unread_only(self, client, sample_user, sample_notifications):
        """Тест за получаване само на непрочетени."""
        response = client.get(
            '/api/notifications?unread_only=true',
            headers={'X-User-ID': str(sample_user)}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert len(data['notifications']) == 2

    def test_get_unread_count(self, client, sample_user, sample_notifications):
        """Тест за броене на непрочетени."""
        response = client.get(
            '/api/notifications/unread-count',
            headers={'X-User-ID': str(sample_user)}
        )

        assert response.status_code == 200
        assert response.get_json()['unread_count'] == 2

    def test_mark_as_read(self, client, sample_user, sample_notifications):
        """Тест за маркиране като прочетено."""
        notification_id = sample_notifications[0]

        response = client.put(
            f'/api/notifications/{notification_id}/read',
            headers={'X-User-ID': str(sample_user)}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['notification']['is_read'] is True

    def test_mark_all_as_read(self, client, sample_user, sample_notifications):
        """Тест за маркиране на всички като прочетени."""
        response = client.put(
            '/api/notifications/read-all',
            headers={'X-User-ID': str(sample_user)}
        )

        assert response.status_code == 200

        # Проверяваме че няма непрочетени
        count_response = client.get(
            '/api/notifications/unread-count',
            headers={'X-User-ID': str(sample_user)}
        )
        assert count_response.get_json()['unread_count'] == 0

    def test_delete_notification(self, client, sample_user, sample_notifications):
        """Тест за изтриване на известие."""
        notification_id = sample_notifications[0]

        response = client.delete(
            f'/api/notifications/{notification_id}',
            headers={'X-User-ID': str(sample_user)}
        )

        assert response.status_code == 200
        assert 'изтрито' in response.get_json()['message']

    def test_notification_unauthorized(self, client):
        """Тест за неавторизиран достъп."""
        response = client.get('/api/notifications')
        assert response.status_code == 401

    def test_notification_forbidden(self, client, sample_user, sample_notifications):
        """Тест за забранен достъп до чуждо известие."""
        # Създаваме друг потребител
        with app.app_context():
            other_user = RegisteredUser(username='other', email='other@test.com')
            other_user.set_password('password123')
            db.session.add(other_user)
            db.session.commit()
            other_id = other_user.id

        # Опитваме се да маркираме чуждо известие
        response = client.put(
            f'/api/notifications/{sample_notifications[0]}/read',
            headers={'X-User-ID': str(other_id)}
        )

        assert response.status_code == 403


class TestNotificationModel:
    """Тестове за Notification модела директно."""

    def test_create_reservation_notification(self, client, sample_user):
        """Тест за фабричен метод за резервация."""
        with app.app_context():
            notification = Notification.create_reservation_notification(
                user_id=sample_user,
                reservation_id=1,
                notification_type=NotificationType.RESERVATION_CONFIRMED,
                service_name='Oil Change'
            )
            db.session.add(notification)
            db.session.commit()

            assert notification.title == 'Потвърдена резервация'
            assert 'Oil Change' in notification.message
            assert notification.related_id == 1

    def test_to_dict(self, client, sample_user):
        """Тест за to_dict метод."""
        with app.app_context():
            notification = Notification(
                user_id=sample_user,
                title='Test',
                message='Test message',
                notification_type=NotificationType.SYSTEM,
                related_id=42
            )
            db.session.add(notification)
            db.session.commit()

            d = notification.to_dict()
            assert d['title'] == 'Test'
            assert d['type'] == 'system'
            assert d['related_id'] == 42
            assert d['is_read'] is False
