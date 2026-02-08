"""
Тестове за Services routes.

Тества:
    - CRUD операции за услуги
    - Търсене на услуги
    - Ревюта за услуги
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from db import db
from models.user import RegisteredUser, Provider, Admin, UserRole
from models.service import Service
from models.review import Review


class TestServicesRoutes(unittest.TestCase):
    """Тестове за services routes."""

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
        db.session.query(Review).delete()
        db.session.query(Service).delete()
        db.session.query(RegisteredUser).delete()
        db.session.commit()

        # Създаваме provider
        self.provider = Provider(username='provider', email='provider@test.com')
        self.provider.set_password('password123')
        db.session.add(self.provider)

        # Създаваме admin
        self.admin = Admin(username='admin', email='admin@test.com')
        self.admin.set_password('admin123')
        db.session.add(self.admin)

        # Създаваме обикновен потребител
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

    # ==================== GET SERVICES TESTS ====================

    def test_get_all_services(self):
        """Тест: GET /services връща всички услуги."""
        response = self.client.get('/api/services')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 1)

    def test_get_service_by_id(self):
        """Тест: GET /services/:id връща услуга."""
        response = self.client.get(f'/api/services/{self.service.id}')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['name'], 'Test Service')

    def test_get_service_not_found(self):
        """Тест: GET /services/:id за несъществуваща услуга."""
        response = self.client.get('/api/services/9999')
        self.assertEqual(response.status_code, 404)

    # ==================== CREATE SERVICE TESTS ====================

    def test_create_service_as_provider(self):
        """Тест: POST /services от provider."""
        response = self.client.post(
            '/api/services',
            headers={'X-User-ID': str(self.provider.id)},
            json={
                'name': 'New Service',
                'category': 'New Category',
                'description': 'Description',
                'price': 50.0
            }
        )
        self.assertEqual(response.status_code, 201)

    def test_create_service_as_admin(self):
        """Тест: POST /services от admin."""
        response = self.client.post(
            '/api/services',
            headers={'X-User-ID': str(self.admin.id)},
            json={
                'name': 'Admin Service',
                'category': 'Admin Category'
            }
        )
        self.assertEqual(response.status_code, 201)

    def test_create_service_unauthorized(self):
        """Тест: POST /services без авторизация."""
        response = self.client.post(
            '/api/services',
            json={'name': 'Test', 'category': 'Test'}
        )
        self.assertEqual(response.status_code, 401)

    def test_create_service_forbidden(self):
        """Тест: POST /services от обикновен потребител."""
        response = self.client.post(
            '/api/services',
            headers={'X-User-ID': str(self.user.id)},
            json={'name': 'Test', 'category': 'Test'}
        )
        self.assertEqual(response.status_code, 403)

    def test_create_service_missing_fields(self):
        """Тест: POST /services без задължителни полета."""
        response = self.client.post(
            '/api/services',
            headers={'X-User-ID': str(self.provider.id)},
            json={'name': 'Only Name'}
        )
        self.assertEqual(response.status_code, 400)

    # ==================== UPDATE SERVICE TESTS ====================

    def test_update_service_as_owner(self):
        """Тест: PUT /services/:id от собственика."""
        response = self.client.put(
            f'/api/services/{self.service.id}',
            headers={'X-User-ID': str(self.provider.id)},
            json={'name': 'Updated Name', 'price': 200.0}
        )
        self.assertEqual(response.status_code, 200)

        updated = db.session.get(Service, self.service.id)
        assert updated is not None
        self.assertEqual(updated.name, 'Updated Name')
        self.assertEqual(updated.price, 200.0)

    def test_update_service_as_admin(self):
        """Тест: PUT /services/:id от admin."""
        response = self.client.put(
            f'/api/services/{self.service.id}',
            headers={'X-User-ID': str(self.admin.id)},
            json={'name': 'Admin Updated'}
        )
        self.assertEqual(response.status_code, 200)

    def test_update_service_unauthorized(self):
        """Тест: PUT /services/:id без авторизация."""
        response = self.client.put(
            f'/api/services/{self.service.id}',
            json={'name': 'Test'}
        )
        self.assertEqual(response.status_code, 401)

    def test_update_service_forbidden(self):
        """Тест: PUT /services/:id от друг потребител."""
        other_provider = Provider(username='other', email='other@test.com')
        other_provider.set_password('pass')
        db.session.add(other_provider)
        db.session.commit()

        response = self.client.put(
            f'/api/services/{self.service.id}',
            headers={'X-User-ID': str(other_provider.id)},
            json={'name': 'Hack'}
        )
        self.assertEqual(response.status_code, 403)

    def test_update_service_not_found(self):
        """Тест: PUT /services/:id за несъществуваща услуга."""
        response = self.client.put(
            '/api/services/9999',
            headers={'X-User-ID': str(self.provider.id)},
            json={'name': 'Test'}
        )
        self.assertEqual(response.status_code, 404)

    def test_update_service_empty_data(self):
        """Тест: PUT /services/:id с празни данни."""
        response = self.client.put(
            f'/api/services/{self.service.id}',
            headers={'X-User-ID': str(self.provider.id)},
            json={}
        )
        # Може да е 200 ако няма промени или 400
        self.assertIn(response.status_code, [200, 400])

    def test_update_service_all_fields(self):
        """Тест: PUT /services/:id с всички полета."""
        response = self.client.put(
            f'/api/services/{self.service.id}',
            headers={'X-User-ID': str(self.provider.id)},
            json={
                'name': 'New Name',
                'description': 'New Description',
                'category': 'New Category',
                'price': 150.0,
                'duration': 90,
                'availability': 'Mon-Fri',
                'image_url': 'http://example.com/image.jpg'
            }
        )
        self.assertEqual(response.status_code, 200)

    # ==================== DELETE SERVICE TESTS ====================

    def test_delete_service_as_owner(self):
        """Тест: DELETE /services/:id от собственика."""
        response = self.client.delete(
            f'/api/services/{self.service.id}',
            headers={'X-User-ID': str(self.provider.id)}
        )
        self.assertEqual(response.status_code, 200)

        deleted = db.session.get(Service, self.service.id)
        self.assertIsNone(deleted)

    def test_delete_service_as_admin(self):
        """Тест: DELETE /services/:id от admin."""
        response = self.client.delete(
            f'/api/services/{self.service.id}',
            headers={'X-User-ID': str(self.admin.id)}
        )
        self.assertEqual(response.status_code, 200)

    def test_delete_service_unauthorized(self):
        """Тест: DELETE /services/:id без авторизация."""
        response = self.client.delete(f'/api/services/{self.service.id}')
        self.assertEqual(response.status_code, 401)

    def test_delete_service_forbidden(self):
        """Тест: DELETE /services/:id от друг потребител."""
        response = self.client.delete(
            f'/api/services/{self.service.id}',
            headers={'X-User-ID': str(self.user.id)}
        )
        self.assertEqual(response.status_code, 403)

    def test_delete_service_not_found(self):
        """Тест: DELETE /services/:id за несъществуваща услуга."""
        response = self.client.delete(
            '/api/services/9999',
            headers={'X-User-ID': str(self.provider.id)}
        )
        self.assertEqual(response.status_code, 404)

    # ==================== SEARCH SERVICE TESTS ====================

    def test_search_services_by_name(self):
        """Тест: GET /services/search?name=..."""
        response = self.client.get('/api/services/search?name=Test')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 1)

    def test_search_services_by_category(self):
        """Тест: GET /services/search?category=..."""
        response = self.client.get('/api/services/search?category=Test')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 1)

    def test_search_services_by_date(self):
        """Тест: GET /services/search?date=..."""
        response = self.client.get('/api/services/search?date=2026-02-10')
        self.assertEqual(response.status_code, 200)

    def test_search_services_invalid_date(self):
        """Тест: GET /services/search?date=invalid"""
        response = self.client.get('/api/services/search?date=invalid')
        self.assertEqual(response.status_code, 400)

    def test_search_services_no_results(self):
        """Тест: GET /services/search с несъвпадащ филтър."""
        response = self.client.get('/api/services/search?name=NonExistent')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 0)

    # ==================== SERVICE REVIEWS TESTS ====================

    def test_get_service_reviews_empty(self):
        """Тест: GET /services/:id/reviews без ревюта."""
        response = self.client.get(f'/api/services/{self.service.id}/reviews')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 0)

    def test_get_service_reviews_with_data(self):
        """Тест: GET /services/:id/reviews с ревюта."""
        review = Review(
            user_id=self.user.id,
            service_id=self.service.id,
            rating=5,
            comment='Great!'
        )
        db.session.add(review)
        db.session.commit()

        response = self.client.get(f'/api/services/{self.service.id}/reviews')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 1)


if __name__ == '__main__':
    unittest.main()
