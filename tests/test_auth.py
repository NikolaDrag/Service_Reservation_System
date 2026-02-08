"""
Тестове за Auth routes.

Тества:
    - Регистрация
    - Вход
    - Изход
    - Профил
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from db import db
from models.user import RegisteredUser, Provider, Admin, UserRole


class TestAuthRoutes(unittest.TestCase):
    """Тестове за auth routes."""

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
        db.session.query(RegisteredUser).delete()
        db.session.commit()

    # ==================== REGISTER TESTS ====================

    def test_register_success(self):
        """Тест: Успешна регистрация."""
        response = self.client.post('/api/auth/register', json={
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertIn('user_id', data)

    def test_register_as_provider(self):
        """Тест: Регистрация като provider."""
        response = self.client.post('/api/auth/register', json={
            'username': 'newprovider',
            'email': 'provider@test.com',
            'password': 'password123',
            'role': 'provider'
        })
        self.assertEqual(response.status_code, 201)

        user = RegisteredUser.query.filter_by(username='newprovider').first()
        assert user is not None
        self.assertEqual(user.role, UserRole.PROVIDER)

    def test_register_as_admin(self):
        """Тест: Регистрация като admin."""
        response = self.client.post('/api/auth/register', json={
            'username': 'newadmin',
            'email': 'admin@test.com',
            'password': 'password123',
            'role': 'admin'
        })
        self.assertEqual(response.status_code, 201)

        user = RegisteredUser.query.filter_by(username='newadmin').first()
        assert user is not None
        self.assertEqual(user.role, UserRole.ADMIN)

    def test_register_missing_fields(self):
        """Тест: Регистрация без задължителни полета."""
        response = self.client.post('/api/auth/register', json={
            'username': 'test'
        })
        self.assertEqual(response.status_code, 400)

    def test_register_duplicate_username(self):
        """Тест: Регистрация с дублиращо се име."""
        self.client.post('/api/auth/register', json={
            'username': 'duplicate',
            'email': 'first@test.com',
            'password': 'password123'
        })

        response = self.client.post('/api/auth/register', json={
            'username': 'duplicate',
            'email': 'second@test.com',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('заето', response.get_json()['error'])

    def test_register_duplicate_email(self):
        """Тест: Регистрация с дублиращ се имейл."""
        self.client.post('/api/auth/register', json={
            'username': 'first',
            'email': 'duplicate@test.com',
            'password': 'password123'
        })

        response = self.client.post('/api/auth/register', json={
            'username': 'second',
            'email': 'duplicate@test.com',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 400)

    # ==================== LOGIN TESTS ====================

    def test_login_success_with_email(self):
        """Тест: Успешен вход с имейл."""
        # Регистрираме потребител
        self.client.post('/api/auth/register', json={
            'username': 'loginuser',
            'email': 'login@test.com',
            'password': 'password123'
        })

        response = self.client.post('/api/auth/login', json={
            'email': 'login@test.com',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('user_id', data)
        self.assertEqual(data['username'], 'loginuser')

    def test_login_success_with_username(self):
        """Тест: Успешен вход с потребителско име."""
        self.client.post('/api/auth/register', json={
            'username': 'loginuser2',
            'email': 'login2@test.com',
            'password': 'password123'
        })

        response = self.client.post('/api/auth/login', json={
            'email': 'loginuser2',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 200)

    def test_login_wrong_password(self):
        """Тест: Вход с грешна парола."""
        self.client.post('/api/auth/register', json={
            'username': 'wrongpass',
            'email': 'wrongpass@test.com',
            'password': 'password123'
        })

        response = self.client.post('/api/auth/login', json={
            'email': 'wrongpass@test.com',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 401)

    def test_login_nonexistent_user(self):
        """Тест: Вход с несъществуващ потребител."""
        response = self.client.post('/api/auth/login', json={
            'email': 'nouser@test.com',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 401)

    def test_login_missing_fields(self):
        """Тест: Вход без задължителни полета."""
        response = self.client.post('/api/auth/login', json={
            'email': 'test@test.com'
        })
        self.assertEqual(response.status_code, 400)

    # ==================== LOGOUT TESTS ====================

    def test_logout(self):
        """Тест: Успешен изход."""
        response = self.client.post('/api/auth/logout')
        self.assertEqual(response.status_code, 200)

    # ==================== PROFILE TESTS ====================

    def test_get_profile_success(self):
        """Тест: Получаване на профил."""
        # Създаваме потребител
        user = RegisteredUser(username='profileuser', email='profile@test.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        response = self.client.get(
            '/api/auth/profile',
            headers={'X-User-ID': str(user.id)}
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['username'], 'profileuser')

    def test_get_profile_unauthorized(self):
        """Тест: Профил без авторизация."""
        response = self.client.get('/api/auth/profile')
        self.assertEqual(response.status_code, 401)

    def test_get_profile_not_found(self):
        """Тест: Профил на несъществуващ потребител."""
        response = self.client.get(
            '/api/auth/profile',
            headers={'X-User-ID': '9999'}
        )
        self.assertEqual(response.status_code, 404)

    def test_update_profile_success(self):
        """Тест: Обновяване на профил."""
        user = RegisteredUser(username='updateuser', email='update@test.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        response = self.client.put(
            '/api/auth/profile',
            headers={'X-User-ID': str(user.id)},
            json={'username': 'newusername'}
        )
        self.assertEqual(response.status_code, 200)

        updated = db.session.get(RegisteredUser, user.id)
        assert updated is not None
        self.assertEqual(updated.username, 'newusername')

    def test_update_profile_unauthorized(self):
        """Тест: Обновяване без авторизация."""
        response = self.client.put(
            '/api/auth/profile',
            json={'username': 'test'}
        )
        self.assertEqual(response.status_code, 401)

    def test_update_profile_not_found(self):
        """Тест: Обновяване на несъществуващ профил."""
        response = self.client.put(
            '/api/auth/profile',
            headers={'X-User-ID': '9999'},
            json={'username': 'test'}
        )
        self.assertEqual(response.status_code, 404)

    def test_update_profile_empty_data(self):
        """Тест: Обновяване с празни данни."""
        user = RegisteredUser(username='nodatauser', email='nodata@test.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

        # Изпращаме празен JSON обект
        response = self.client.put(
            '/api/auth/profile',
            headers={'X-User-ID': str(user.id)},
            json={}
        )
        # Може да е 200 или 400 в зависимост от имплементацията
        self.assertIn(response.status_code, [200, 400])

    def test_update_profile_duplicate_username(self):
        """Тест: Обновяване с дублиращо се име."""
        user1 = RegisteredUser(username='user1', email='user1@test.com')
        user1.set_password('password123')
        user2 = RegisteredUser(username='user2', email='user2@test.com')
        user2.set_password('password123')
        db.session.add_all([user1, user2])
        db.session.commit()

        response = self.client.put(
            '/api/auth/profile',
            headers={'X-User-ID': str(user2.id)},
            json={'username': 'user1'}
        )
        self.assertEqual(response.status_code, 400)


if __name__ == '__main__':
    unittest.main()
