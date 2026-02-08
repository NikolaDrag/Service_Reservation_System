"""Маршрути за любими услуги."""
from flask import Blueprint, request, jsonify, Response
from db import db
from models.user import RegisteredUser

favorites_bp = Blueprint('favorites', __name__)


def _get_current_user() -> RegisteredUser | None:
    """Помощна функция за взимане на текущия потребител."""
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return None
    return db.session.get(RegisteredUser, int(user_id))


@favorites_bp.route('', methods=['GET'])
def get_favorites() -> tuple[Response, int]:
    """Връща любимите услуги на потребителя."""
    user = _get_current_user()
    if not user:
        return jsonify({'error': 'Не сте влезли в системата'}), 401

    return jsonify(user.get_favorites()), 200


@favorites_bp.route('', methods=['POST'])
def add_favorite() -> tuple[Response, int]:
    """Добавя услуга към любими."""
    user = _get_current_user()
    if not user:
        return jsonify({'error': 'Не сте влезли в системата'}), 401

    data = request.get_json()
    if not data or 'service_id' not in data:
        return jsonify({'error': 'Липсва service_id'}), 400

    try:
        success = user.add_favorite(data['service_id'])
        if not success:
            return jsonify({'error': 'Вече е в любими'}), 400
        return jsonify({'message': 'Добавено към любими'}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 404


@favorites_bp.route('/<int:service_id>', methods=['DELETE'])
def remove_favorite(service_id: int) -> tuple[Response, int]:
    """Премахва услуга от любими."""
    user = _get_current_user()
    if not user:
        return jsonify({'error': 'Не сте влезли в системата'}), 401

    success = user.remove_favorite(service_id)
    if not success:
        return jsonify({'error': 'Не е в любими'}), 404

    return jsonify({'message': 'Премахнато от любими'}), 200
