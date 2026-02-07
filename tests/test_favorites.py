"""
Тестове за Favorites (любими услуги).
"""
import pytest
from main import app
from db import db
from models.user import RegisteredUser, Provider
from models.service import Service
from models.favorite import Favorite


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
def sample_data(client):
    """Създава примерни данни за тестове."""
    with app.app_context():
        # Създаваме потребител
        user = RegisteredUser(username='testuser', email='test@test.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        user_id = user.id

        # Създаваме provider
        provider = Provider(username='provider1', email='provider@test.com')
        provider.set_password('password123')
        db.session.add(provider)
        db.session.commit()
        provider_id = provider.id

        # Създаваме услуга
        service = Service(
            name='Oil Change',
            category='Maintenance',
            provider_id=provider_id,
            description='Full oil change service',
            price=50.0,
            duration=30
        )
        db.session.add(service)
        db.session.commit()
        service_id = service.id

        return {
            'user_id': user_id,
            'provider_id': provider_id,
            'service_id': service_id
        }


class TestFavorite:
    """Тестове за модела Favorite."""

    def test_add_favorite(self, client, sample_data):
        """Тест добавяне на любима услуга."""
        response = client.post(
            '/api/favorites',
            headers={'X-User-ID': str(sample_data['user_id'])},
            json={'service_id': sample_data['service_id']}
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data['message'] == 'Услугата е добавена към любими'
        assert 'favorite' in data

    def test_add_duplicate_favorite(self, client, sample_data):
        """Тест за дублираща се любима услуга."""
        # Добавяме първия път
        client.post(
            '/api/favorites',
            headers={'X-User-ID': str(sample_data['user_id'])},
            json={'service_id': sample_data['service_id']}
        )

        # Опитваме се да добавим отново
        response = client.post(
            '/api/favorites',
            headers={'X-User-ID': str(sample_data['user_id'])},
            json={'service_id': sample_data['service_id']}
        )

        assert response.status_code == 400
        assert 'вече е в любими' in response.get_json()['error']

    def test_get_favorites(self, client, sample_data):
        """Тест за получаване на списък с любими."""
        # Добавяме любима услуга
        client.post(
            '/api/favorites',
            headers={'X-User-ID': str(sample_data['user_id'])},
            json={'service_id': sample_data['service_id']}
        )

        # Взимаме списъка
        response = client.get(
            '/api/favorites',
            headers={'X-User-ID': str(sample_data['user_id'])}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 1
        assert data[0]['service_id'] == sample_data['service_id']

    def test_remove_favorite(self, client, sample_data):
        """Тест за премахване на любима услуга."""
        # Добавяме
        client.post(
            '/api/favorites',
            headers={'X-User-ID': str(sample_data['user_id'])},
            json={'service_id': sample_data['service_id']}
        )

        # Премахваме
        response = client.delete(
            f'/api/favorites/{sample_data["service_id"]}',
            headers={'X-User-ID': str(sample_data['user_id'])}
        )

        assert response.status_code == 200
        assert 'премахната от любими' in response.get_json()['message']

    def test_check_favorite_true(self, client, sample_data):
        """Тест за проверка дали услуга е в любими (да)."""
        # Добавяме
        client.post(
            '/api/favorites',
            headers={'X-User-ID': str(sample_data['user_id'])},
            json={'service_id': sample_data['service_id']}
        )

        # Проверяваме
        response = client.get(
            f'/api/favorites/check/{sample_data["service_id"]}',
            headers={'X-User-ID': str(sample_data['user_id'])}
        )

        assert response.status_code == 200
        assert response.get_json()['is_favorite'] is True

    def test_check_favorite_false(self, client, sample_data):
        """Тест за проверка дали услуга е в любими (не)."""
        response = client.get(
            f'/api/favorites/check/{sample_data["service_id"]}',
            headers={'X-User-ID': str(sample_data['user_id'])}
        )

        assert response.status_code == 200
        assert response.get_json()['is_favorite'] is False

    def test_favorites_unauthorized(self, client):
        """Тест за неавторизиран достъп."""
        response = client.get('/api/favorites')

        assert response.status_code == 401
