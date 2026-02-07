"""
Тестове за свободни часове и история на обслужванията.
"""
import pytest
from datetime import datetime, timedelta
from main import app
from db import db
from models.user import RegisteredUser, Provider
from models.service import Service
from models.reservation import Reservation, ReservationStatus


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
    """Създава примерни данни."""
    with app.app_context():
        # Потребител
        user = RegisteredUser(username='customer', email='customer@test.com')
        user.set_password('password123')
        db.session.add(user)

        # Provider
        provider = Provider(username='autoservice', email='service@test.com')
        provider.set_password('password123')
        db.session.add(provider)
        db.session.commit()

        # Услуга с работно време и продължителност
        service = Service(
            name='Brake Repair',
            category='Repair',
            provider_id=provider.id,
            description='Full brake inspection and repair',
            price=150.0,
            duration=90  # 90 минути
        )
        db.session.add(service)
        db.session.commit()

        return {
            'user_id': user.id,
            'provider_id': provider.id,
            'service_id': service.id
        }


class TestAvailableSlots:
    """Тестове за свободни часове."""

    def test_get_available_slots(self, client, sample_data):
        """Тест за получаване на свободни часове."""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

        response = client.get(
            f'/api/reservations/available-slots?service_id={sample_data["service_id"]}&date={tomorrow}'
        )

        assert response.status_code == 200
        data = response.get_json()
        assert 'available_slots' in data
        assert 'working_hours' in data
        assert len(data['available_slots']) > 0  # Трябва да има свободни часове

    def test_available_slots_excludes_booked(self, client, sample_data):
        """Тест че заетите часове са изключени."""
        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow_str = tomorrow.strftime('%Y-%m-%d')

        # Създаваме резервация за 10:00
        with app.app_context():
            reservation = Reservation(
                datetime=tomorrow.replace(hour=10, minute=0, second=0, microsecond=0),
                customer_id=sample_data['user_id'],
                provider_id=sample_data['provider_id'],
                service_id=sample_data['service_id'],
                status=ReservationStatus.CONFIRMED
            )
            db.session.add(reservation)
            db.session.commit()

        # Проверяваме свободните часове
        response = client.get(
            f'/api/reservations/available-slots?service_id={sample_data["service_id"]}&date={tomorrow_str}'
        )

        data = response.get_json()
        assert '10:00' not in data['available_slots']  # 10:00 e зает

    def test_available_slots_missing_params(self, client):
        """Тест за липсващи параметри."""
        response = client.get('/api/reservations/available-slots')
        assert response.status_code == 400

    def test_available_slots_invalid_date(self, client, sample_data):
        """Тест за невалидна дата."""
        response = client.get(
            f'/api/reservations/available-slots?service_id={sample_data["service_id"]}&date=invalid'
        )
        assert response.status_code == 400
        # Проверяваме за "Invalid" или "Невалиден"
        error_msg = response.get_json()['error'].lower()
        assert 'invalid' in error_msg or 'невалиден' in error_msg

    def test_available_slots_nonexistent_service(self, client):
        """Тест за несъществуваща услуга."""
        response = client.get(
            '/api/reservations/available-slots?service_id=9999&date=2026-01-01'
        )
        assert response.status_code == 404


class TestReservationHistory:
    """Тестове за история на обслужванията."""

    def test_get_history_as_customer(self, client, sample_data):
        """Тест за история като клиент."""
        # Създаваме завършена резервация
        with app.app_context():
            reservation = Reservation(
                datetime=datetime.now() - timedelta(days=7),
                customer_id=sample_data['user_id'],
                provider_id=sample_data['provider_id'],
                service_id=sample_data['service_id'],
                status=ReservationStatus.COMPLETED,
                notes='Brake pads replaced'
            )
            db.session.add(reservation)
            db.session.commit()

        response = client.get(
            '/api/reservations/history',
            headers={'X-User-ID': str(sample_data['user_id'])}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert 'history' in data
        assert len(data['history']) == 1
        assert data['history'][0]['status'] == 'Completed'

    def test_get_history_as_provider(self, client, sample_data):
        """Тест за история като сервиз."""
        # Създаваме завършена резервация
        with app.app_context():
            reservation = Reservation(
                datetime=datetime.now() - timedelta(days=7),
                customer_id=sample_data['user_id'],
                provider_id=sample_data['provider_id'],
                service_id=sample_data['service_id'],
                status=ReservationStatus.COMPLETED
            )
            db.session.add(reservation)
            db.session.commit()

        response = client.get(
            '/api/reservations/history?role=provider',
            headers={'X-User-ID': str(sample_data['provider_id'])}
        )

        assert response.status_code == 200
        data = response.get_json()
        assert len(data['history']) == 1

    def test_history_excludes_pending(self, client, sample_data):
        """Тест че историята НЕ включва чакащи резервации."""
        with app.app_context():
            # Pending резервация
            pending = Reservation(
                datetime=datetime.now() + timedelta(days=1),
                customer_id=sample_data['user_id'],
                provider_id=sample_data['provider_id'],
                service_id=sample_data['service_id'],
                status=ReservationStatus.PENDING
            )
            # Completed резервация
            completed = Reservation(
                datetime=datetime.now() - timedelta(days=7),
                customer_id=sample_data['user_id'],
                provider_id=sample_data['provider_id'],
                service_id=sample_data['service_id'],
                status=ReservationStatus.COMPLETED
            )
            db.session.add_all([pending, completed])
            db.session.commit()

        response = client.get(
            '/api/reservations/history',
            headers={'X-User-ID': str(sample_data['user_id'])}
        )

        data = response.get_json()
        # Само completed трябва да е в историята
        assert data['total_count'] == 1

    def test_history_unauthorized(self, client):
        """Тест за неавторизиран достъп."""
        response = client.get('/api/reservations/history')
        assert response.status_code == 401


class TestProblemImage:
    """Тестове за снимка на проблема."""

    def test_create_reservation_with_image(self, client, sample_data):
        """Тест за създаване на резервация със снимка."""
        tomorrow = (datetime.now() + timedelta(days=1)).isoformat()

        response = client.post(
            '/api/reservations',
            headers={'X-User-ID': str(sample_data['user_id'])},
            json={
                'datetime': tomorrow,
                'service_id': sample_data['service_id'],
                'notes': 'Strange noise when braking',
                'problem_image_url': 'https://example.com/brake-problem.jpg'
            }
        )

        assert response.status_code == 201

    def test_get_reservation_with_image(self, client, sample_data):
        """Тест за получаване на резервация със снимка."""
        with app.app_context():
            reservation = Reservation(
                datetime=datetime.now() + timedelta(days=1),
                customer_id=sample_data['user_id'],
                provider_id=sample_data['provider_id'],
                service_id=sample_data['service_id'],
                notes='Engine light on',
                problem_image_url='https://example.com/engine-light.jpg'
            )
            db.session.add(reservation)
            db.session.commit()
            reservation_id = reservation.id

        response = client.get(f'/api/reservations/{reservation_id}')

        assert response.status_code == 200
        data = response.get_json()
        assert data['problem_image_url'] == 'https://example.com/engine-light.jpg'
        assert data['notes'] == 'Engine light on'
