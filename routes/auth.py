from flask import Blueprint, request, jsonify, Response
from werkzeug.security import generate_password_hash, check_password_hash
from typing import Any
from db import db
from models.user import User, UserRole

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register() -> tuple[Response, int]:
    data: dict[str, Any] | None = request.get_json()
    
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Липсват задължителни полета'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Потребителското име е заето'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Имейлът е зает'}), 400
    
    user = User(
        username=data['username'],
        email=data['email'],
        password_hash=generate_password_hash(data['password']),
        role=UserRole(data.get('role', 'user'))
    )
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'message': 'Регистрацията е успешна', 'user_id': user.id}), 201


@auth_bp.route('/login', methods=['POST'])
def login() -> tuple[Response, int]:
    data: dict[str, Any] | None = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Липсват имейл или парола'}), 400
    
    user: User | None = User.query.filter_by(email=data['email']).first()
    
    if not user or not check_password_hash(user.password_hash, data['password']):
        return jsonify({'error': 'Грешен имейл или парола'}), 401
    
    return jsonify({
        'message': 'Успешен вход',
        'user_id': user.id,
        'username': user.username,
        'role': user.role.value
    }), 200


@auth_bp.route('/logout', methods=['POST'])
def logout() -> tuple[Response, int]:
    return jsonify({'message': 'Успешен изход'}), 200
