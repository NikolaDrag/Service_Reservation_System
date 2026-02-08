"""
Тестове за Reservations routes.

Тества:
    - CRUD операции за резервации
    - Available slots
    - History
    - Status updates
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
from models.reservation import Reservation, ReservationStatus


def make_reservation(customer_id: int, provider_id: int, service_id: int,
                     scheduled_time: datetime,
                     status: ReservationStatus = ReservationStatus.PENDING) -> Reservation:
    """Helper function to create reservations."""
    return Reservation(
        datetime=scheduled_time,
        customer_id=customer_id,
        provider_id=provider_id,
        service_id=service_id,
        status=status
    )


class TestReservationsRoutes(unittest.TestCase):
    """Тестове за reservations routes."""

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

    # ==================== GET RESERVATIONS TESTS ====================

    def test_get_all_reservations(self):
        """Тест: GET /reservations връща всички резервации."""
        reservation = make_reservation(
            customer_id=self.user.id,
            provider_id=self.provider.id,
            service_id=self.service.id,
            scheduled_time=datetime.now() + timedelta(days=1)
        )
        db.session.add(reservation)
        db.session.commit()

        response = self.client.get('/api/reservations')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 1)

    def test_get_reservations_filter_by_user_id(self):
        """Тест: GET /reservations?user_id=... филтрира по клиент."""
        reservation = make_reservation(
            customer_id=self.user.id,
            provider_id=self.provider.id,
            service_id=self.service.id,
            scheduled_time=datetime.now() + timedelta(days=1)
        )
        db.session.add(reservation)
        db.session.commit()

        response = self.client.get(f'/api/reservations?user_id={self.user.id}')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 1)

    def test_get_reservations_filter_by_provider_id(self):
        """Тест: GET /reservations?provider_id=... филтрира по доставчик."""
        reservation = make_reservation(
            customer_id=self.user.id,
            provider_id=self.provider.id,
            service_id=self.service.id,
            scheduled_time=datetime.now() + timedelta(days=1)
        )
        db.session.add(reservation)
        db.session.commit()

        response = self.client.get(f'/api/reservations?provider_id={self.provider.id}')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 1)

    def test_get_reservations_filter_by_status(self):
        """Тест: GET /reservations?status=... филтрира по статус."""
        reservation = make_reservation(
            customer_id=self.user.id,
            provider_id=self.provider.id,
            service_id=self.service.id,
            scheduled_time=datetime.now() + timedelta(days=1),
            status=ReservationStatus.CONFIRMED
        )
        db.session.add(reservation)
        db.session.commit()

        response = self.client.get('/api/reservations?status=Confirmed')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 1)

    def test_get_reservations_invalid_status(self):
        """Тест: GET /reservations?status=invalid игнорира невалиден статус."""
        reservation = make_reservation(
            customer_id=self.user.id,
            provider_id=self.provider.id,
            service_id=self.service.id,
            scheduled_time=datetime.now() + timedelta(days=1)
        )
        db.session.add(reservation)
        db.session.commit()

        response = self.client.get('/api/reservations?status=InvalidStatus')
        self.assertEqual(response.status_code, 200)

    def test_get_reservation_by_id(self):
        """Тест: GET /reservations/:id връща резервация."""
        reservation = make_reservation(
            customer_id=self.user.id,
            provider_id=self.provider.id,
            service_id=self.service.id,
            scheduled_time=datetime.now() + timedelta(days=1)
        )
        db.session.add(reservation)
        db.session.commit()

        response = self.client.get(f'/api/reservations/{reservation.id}')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['id'], reservation.id)

    def test_get_reservation_not_found(self):
        """Тест: GET /reservations/:id за несъществуваща резервация."""
        response = self.client.get('/api/reservations/9999')
        self.assertEqual(response.status_code, 404)

    # ==================== CREATE RESERVATION TESTS ====================

    def test_create_reservation(self):
        """Тест: POST /reservations създава резервация."""
        future_date = (datetime.now() + timedelta(days=1)).isoformat()
        response = self.client.post(
            '/api/reservations',
            headers={'X-User-ID': str(self.user.id)},
            json={
                'service_id': self.service.id,
                'datetime': future_date,
                'notes': 'Test notes'
            }
        )
        self.assertEqual(response.status_code, 201)

    def test_create_reservation_unauthorized(self):
        """Тест: POST /reservations без авторизация."""
        future_date = (datetime.now() + timedelta(days=1)).isoformat()
        response = self.client.post(
            '/api/reservations',
            json={
                'service_id': self.service.id,
                'datetime': future_date
            }
        )
        self.assertEqual(response.status_code, 401)

    def test_create_reservation_user_not_found(self):
        """Тест: POST /reservations с несъществуващ потребител."""
        future_date = (datetime.now() + timedelta(days=1)).isoformat()
        response = self.client.post(
            '/api/reservations',
            headers={'X-User-ID': '9999'},
            json={
                'service_id': self.service.id,
                'datetime': future_date
            }
        )
        self.assertEqual(response.status_code, 404)

    def test_create_reservation_no_data(self):
        """Тест: POST /reservations без данни."""
        response = self.client.post(
            '/api/reservations',
            headers={'X-User-ID': str(self.user.id)},
            json={}
        )
        self.assertEqual(response.status_code, 400)

    def test_create_reservation_missing_fields(self):
        """Тест: POST /reservations без задължителни полета."""
        response = self.client.post(
            '/api/reservations',
            headers={'X-User-ID': str(self.user.id)},
            json={'notes': 'Only notes'}
        )
        self.assertEqual(response.status_code, 400)

    # ==================== UPDATE RESERVATION TESTS ====================

    def test_update_reservation(self):
        """Тест: PUT /reservations/:id обновява резервация."""
        reservation = make_reservation(
            customer_id=self.user.id,
            provider_id=self.provider.id,
            service_id=self.service.id,
            scheduled_time=datetime.now() + timedelta(days=1)
        )
        db.session.add(reservation)
        db.session.commit()

        new_date = (datetime.now() + timedelta(days=2)).isoformat()
        response = self.client.put(
            f'/api/reservations/{reservation.id}',
            json={
                'datetime': new_date,
                'notes': 'Updated notes',
                'problem_image_url': 'http://example.com/image.jpg'
            }
        )
        self.assertEqual(response.status_code, 200)

    def test_update_reservation_not_found(self):
        """Тест: PUT /reservations/:id за несъществуваща резервация."""
        response = self.client.put(
            '/api/reservations/9999',
            json={'notes': 'Test'}
        )
        self.assertEqual(response.status_code, 404)

    def test_update_reservation_no_data(self):
        """Тест: PUT /reservations/:id без данни."""
        reservation = make_reservation(
            customer_id=self.user.id,
            provider_id=self.provider.id,
            service_id=self.service.id,
            scheduled_time=datetime.now() + timedelta(days=1)
        )
        db.session.add(reservation)
        db.session.commit()

        response = self.client.put(
            f'/api/reservations/{reservation.id}',
            json={}
        )
        # Може да е 200 ако празен JSON е валиден или 400
        self.assertIn(response.status_code, [200, 400])

    # ==================== UPDATE STATUS TESTS ====================

    def test_update_reservation_status(self):
        """Тест: PUT /reservations/:id/status обновява статуса."""
        reservation = make_reservation(
            customer_id=self.user.id,
            provider_id=self.provider.id,
            service_id=self.service.id,
            scheduled_time=datetime.now() + timedelta(days=1)
        )
        db.session.add(reservation)
        db.session.commit()

        response = self.client.put(
            f'/api/reservations/{reservation.id}/status',
            json={'status': 'Confirmed'}
        )
        self.assertEqual(response.status_code, 200)

    def test_update_reservation_status_not_found(self):
        """Тест: PUT /reservations/:id/status за несъществуваща резервация."""
        response = self.client.put(
            '/api/reservations/9999/status',
            json={'status': 'Confirmed'}
        )
        self.assertEqual(response.status_code, 404)

    def test_update_reservation_status_missing(self):
        """Тест: PUT /reservations/:id/status без статус."""
        reservation = make_reservation(
            customer_id=self.user.id,
            provider_id=self.provider.id,
            service_id=self.service.id,
            scheduled_time=datetime.now() + timedelta(days=1)
        )
        db.session.add(reservation)
        db.session.commit()

        response = self.client.put(
            f'/api/reservations/{reservation.id}/status',
            json={}
        )
        self.assertEqual(response.status_code, 400)

    def test_update_reservation_status_invalid(self):
        """Тест: PUT /reservations/:id/status с невалиден статус."""
        reservation = make_reservation(
            customer_id=self.user.id,
            provider_id=self.provider.id,
            service_id=self.service.id,
            scheduled_time=datetime.now() + timedelta(days=1)
        )
        db.session.add(reservation)
        db.session.commit()

        response = self.client.put(
            f'/api/reservations/{reservation.id}/status',
            json={'status': 'InvalidStatus'}
        )
        self.assertEqual(response.status_code, 400)

    # ==================== DELETE RESERVATION TESTS ====================

    def test_delete_reservation(self):
        """Тест: DELETE /reservations/:id изтрива резервация."""
        reservation = make_reservation(
            customer_id=self.user.id,
            provider_id=self.provider.id,
            service_id=self.service.id,
            scheduled_time=datetime.now() + timedelta(days=1)
        )
        db.session.add(reservation)
        db.session.commit()

        response = self.client.delete(f'/api/reservations/{reservation.id}')
        self.assertEqual(response.status_code, 200)

    def test_delete_reservation_not_found(self):
        """Тест: DELETE /reservations/:id за несъществуваща резервация."""
        response = self.client.delete('/api/reservations/9999')
        self.assertEqual(response.status_code, 404)

    # ==================== AVAILABLE SLOTS TESTS ====================

    def test_get_available_slots(self):
        """Тест: GET /reservations/available-slots връща свободни часове."""
        future_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        response = self.client.get(
            f'/api/reservations/available-slots?service_id={self.service.id}&date={future_date}'
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('available_slots', data)

    def test_get_available_slots_missing_params(self):
        """Тест: GET /reservations/available-slots без параметри."""
        response = self.client.get('/api/reservations/available-slots')
        self.assertEqual(response.status_code, 400)

    def test_get_available_slots_service_not_found(self):
        """Тест: GET /reservations/available-slots с несъществуваща услуга."""
        future_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        response = self.client.get(
            f'/api/reservations/available-slots?service_id=9999&date={future_date}'
        )
        self.assertEqual(response.status_code, 404)

    def test_get_available_slots_invalid_date(self):
        """Тест: GET /reservations/available-slots с невалидна дата."""
        response = self.client.get(
            f'/api/reservations/available-slots?service_id={self.service.id}&date=invalid'
        )
        self.assertEqual(response.status_code, 400)

    def test_get_available_slots_with_existing_reservation(self):
        """Тест: GET /reservations/available-slots с съществуваща резервация."""
        future_date = datetime.now() + timedelta(days=1)
        future_date = future_date.replace(hour=10, minute=0, second=0, microsecond=0)
        
        reservation = make_reservation(
            customer_id=self.user.id,
            provider_id=self.provider.id,
            service_id=self.service.id,
            scheduled_time=future_date
        )
        db.session.add(reservation)
        db.session.commit()

        date_str = future_date.strftime('%Y-%m-%d')
        response = self.client.get(
            f'/api/reservations/available-slots?service_id={self.service.id}&date={date_str}'
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        # 10:00 не трябва да е в списъка
        self.assertNotIn('10:00', data['available_slots'])

    # ==================== HISTORY TESTS ====================

    def test_get_reservation_history_as_customer(self):
        """Тест: GET /reservations/history като клиент."""
        reservation = make_reservation(
            customer_id=self.user.id,
            provider_id=self.provider.id,
            service_id=self.service.id,
            scheduled_time=datetime.now() - timedelta(days=1),
            status=ReservationStatus.COMPLETED
        )
        db.session.add(reservation)
        db.session.commit()

        response = self.client.get(
            '/api/reservations/history',
            headers={'X-User-ID': str(self.user.id)}
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('history', data)
        self.assertEqual(len(data['history']), 1)

    def test_get_reservation_history_as_provider(self):
        """Тест: GET /reservations/history?role=provider като доставчик."""
        reservation = make_reservation(
            customer_id=self.user.id,
            provider_id=self.provider.id,
            service_id=self.service.id,
            scheduled_time=datetime.now() - timedelta(days=1),
            status=ReservationStatus.COMPLETED
        )
        db.session.add(reservation)
        db.session.commit()

        response = self.client.get(
            '/api/reservations/history?role=provider',
            headers={'X-User-ID': str(self.provider.id)}
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('history', data)
        self.assertEqual(len(data['history']), 1)

    def test_get_reservation_history_unauthorized(self):
        """Тест: GET /reservations/history без авторизация."""
        response = self.client.get('/api/reservations/history')
        self.assertEqual(response.status_code, 401)


if __name__ == '__main__':
    unittest.main()
