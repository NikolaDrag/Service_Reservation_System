"""
Тестове за Reviews routes.

Тества:
    - CRUD операции за ревюта
    - Филтрация по service_id
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from db import db
from models.user import RegisteredUser, Provider, Admin
from models.service import Service
from models.review import Review


class TestReviewsRoutes(unittest.TestCase):
    """Тестове за reviews routes."""

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

    # ==================== GET REVIEWS TESTS ====================

    def test_get_all_reviews(self):
        """Тест: GET /reviews връща всички ревюта."""
        review = Review(
            user_id=self.user.id,
            service_id=self.service.id,
            rating=5,
            comment='Great!'
        )
        db.session.add(review)
        db.session.commit()

        response = self.client.get('/api/reviews')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 1)

    def test_get_reviews_by_service_id(self):
        """Тест: GET /reviews?service_id=... филтрира по услуга."""
        review = Review(
            user_id=self.user.id,
            service_id=self.service.id,
            rating=4,
            comment='Good!'
        )
        db.session.add(review)
        db.session.commit()

        response = self.client.get(f'/api/reviews?service_id={self.service.id}')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 1)

    def test_get_reviews_by_wrong_service_id(self):
        """Тест: GET /reviews?service_id=... с грешен id."""
        review = Review(
            user_id=self.user.id,
            service_id=self.service.id,
            rating=4
        )
        db.session.add(review)
        db.session.commit()

        response = self.client.get('/api/reviews?service_id=9999')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data), 0)

    def test_get_review_by_id(self):
        """Тест: GET /reviews/:id връща ревю."""
        review = Review(
            user_id=self.user.id,
            service_id=self.service.id,
            rating=5
        )
        db.session.add(review)
        db.session.commit()

        response = self.client.get(f'/api/reviews/{review.id}')
        self.assertEqual(response.status_code, 200)

    def test_get_review_not_found(self):
        """Тест: GET /reviews/:id за несъществуващо ревю."""
        response = self.client.get('/api/reviews/9999')
        self.assertEqual(response.status_code, 404)

    # ==================== CREATE REVIEW TESTS ====================

    def test_create_review(self):
        """Тест: POST /reviews създава ревю."""
        response = self.client.post(
            '/api/reviews',
            headers={'X-User-ID': str(self.user.id)},
            json={
                'service_id': self.service.id,
                'rating': 5,
                'comment': 'Excellent service!'
            }
        )
        self.assertEqual(response.status_code, 201)

    def test_create_review_minimal(self):
        """Тест: POST /reviews с минимални данни."""
        response = self.client.post(
            '/api/reviews',
            headers={'X-User-ID': str(self.user.id)},
            json={
                'service_id': self.service.id,
                'rating': 3
            }
        )
        self.assertEqual(response.status_code, 201)

    def test_create_review_unauthorized(self):
        """Тест: POST /reviews без авторизация."""
        response = self.client.post(
            '/api/reviews',
            json={'service_id': self.service.id, 'rating': 5}
        )
        self.assertEqual(response.status_code, 401)

    def test_create_review_missing_service_id(self):
        """Тест: POST /reviews без service_id."""
        response = self.client.post(
            '/api/reviews',
            headers={'X-User-ID': str(self.user.id)},
            json={'rating': 5}
        )
        self.assertEqual(response.status_code, 400)

    def test_create_review_missing_rating(self):
        """Тест: POST /reviews без rating."""
        response = self.client.post(
            '/api/reviews',
            headers={'X-User-ID': str(self.user.id)},
            json={'service_id': self.service.id}
        )
        self.assertEqual(response.status_code, 400)

    # ==================== DELETE REVIEW TESTS ====================

    def test_delete_review(self):
        """Тест: DELETE /reviews/:id изтрива ревю."""
        review = Review(
            user_id=self.user.id,
            service_id=self.service.id,
            rating=5
        )
        db.session.add(review)
        db.session.commit()

        response = self.client.delete(f'/api/reviews/{review.id}')
        self.assertEqual(response.status_code, 200)

        deleted = db.session.get(Review, review.id)
        self.assertIsNone(deleted)

    def test_delete_review_not_found(self):
        """Тест: DELETE /reviews/:id за несъществуващо ревю."""
        response = self.client.delete('/api/reviews/9999')
        self.assertEqual(response.status_code, 404)


if __name__ == '__main__':
    unittest.main()
