"""Маршрути за любими услуги."""
from flask import Blueprint, request, jsonify, Response
from db import db
from models.favorite import Favorite
from models.service import Service
from models.user import RegisteredUser

favorites_bp = Blueprint('favorites', __name__)


@favorites_bp.route('', methods=['GET'])
def get_favorites() -> tuple[Response, int]:
    """Връща любимите услуги на потребителя."""
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({'error': 'Не сте влезли в системата'}), 401

    favorites = Favorite.query.filter_by(user_id=int(user_id)).all()
    return jsonify([f.to_dict() for f in favorites]), 200


@favorites_bp.route('', methods=['POST'])
def add_favorite() -> tuple[Response, int]:
    """Добавя услуга към любими."""
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({'error': 'Не сте влезли в системата'}), 401

    data = request.get_json()
    if not data or 'service_id' not in data:
        return jsonify({'error': 'Липсва service_id'}), 400

    service = db.session.get(Service, data['service_id'])
    if not service:
        return jsonify({'error': 'Услугата не съществува'}), 404

    existing = Favorite.query.filter_by(
        user_id=int(user_id), service_id=data['service_id']
    ).first()
    if existing:
        return jsonify({'error': 'Вече е в любими'}), 400

    favorite = Favorite(user_id=int(user_id), service_id=data['service_id'])
    db.session.add(favorite)
    db.session.commit()

    return jsonify({'message': 'Добавено към любими'}), 201


@favorites_bp.route('/<int:service_id>', methods=['DELETE'])
def remove_favorite(service_id: int) -> tuple[Response, int]:
    """Премахва услуга от любими."""
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({'error': 'Не сте влезли в системата'}), 401

    favorite = Favorite.query.filter_by(
        user_id=int(user_id), service_id=service_id
    ).first()
    if not favorite:
        return jsonify({'error': 'Не е в любими'}), 404

    db.session.delete(favorite)
    db.session.commit()

    return jsonify({'message': 'Премахнато от любими'}), 200
