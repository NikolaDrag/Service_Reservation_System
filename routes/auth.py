from typing import Any

from flask import Blueprint, request, jsonify, Response

from db import db
from models.user import RegisteredUser, Provider, Admin, UserRole

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register() -> tuple[Response, int]:
    """
    Регистрация на нов потребител.

    Очаква JSON:
        username: Потребителско име
        email: Имейл
        password: Парола
        role: Роля (незадължително, по подразбиране 'user')
    """
    data: dict[str, Any] | None = request.get_json()

    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Липсват задължителни полета'}), 400

    if RegisteredUser.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Потребителското име е заето'}), 400

    if RegisteredUser.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Имейлът е зает'}), 400

    role_str = data.get('role', 'user')
    role = UserRole(role_str)

    if role == UserRole.ADMIN:
        user = Admin(username=data['username'], email=data['email'], role=role)
    elif role == UserRole.PROVIDER:
        user = Provider(username=data['username'], email=data['email'], role=role)
    else:
        user = RegisteredUser(username=data['username'], email=data['email'], role=role)

    user.set_password(data['password'])

    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'Регистрацията е успешна', 'user_id': user.id}), 201


@auth_bp.route('/login', methods=['POST'])
def login() -> tuple[Response, int]:
    """
    Вход в системата.

    Очаква JSON:
        email: Имейл ИЛИ потребителско име
        password: Парола
    """
    data: dict[str, Any] | None = request.get_json()

    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Липсват имейл или парола'}), 400

    user = RegisteredUser.login(data['email'], data['password'])

    if not user:
        return jsonify({'error': 'Грешен имейл/потребителско име или парола'}), 401

    return jsonify({
        'message': 'Успешен вход',
        'user_id': user.id,
        'username': user.username,
        'role': user.role.value
    }), 200


@auth_bp.route('/logout', methods=['POST'])
def logout() -> tuple[Response, int]:
    """Изход от системата."""
    return jsonify({'message': 'Успешен изход'}), 200


@auth_bp.route('/profile', methods=['GET'])
def get_profile() -> tuple[Response, int]:
    """
    Връща профила на текущия потребител.
    """
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({'error': 'Не сте влезли в системата'}), 401

    user = db.session.get(RegisteredUser, int(user_id))
    if not user:
        return jsonify({'error': 'Потребителят не е намерен'}), 404

    return jsonify(user.to_dict()), 200


@auth_bp.route('/profile', methods=['PUT'])
def update_profile() -> tuple[Response, int]:
    """
    Обновява профила на текущия потребител.

    Очаква header: X-User-ID
    Очаква JSON: username, email (незадължителни)
    """
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({'error': 'Не сте влезли в системата'}), 401

    user = db.session.get(RegisteredUser, int(user_id))
    if not user:
        return jsonify({'error': 'Потребителят не е намерен'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Няма данни за обновяване'}), 400

    try:
        user.update_profile(
            new_username=data.get('username'),
            new_email=data.get('email')
        )
        return jsonify({'message': 'Профилът е обновен'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
