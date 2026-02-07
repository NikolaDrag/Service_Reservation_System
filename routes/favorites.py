"""
Маршрути за любими услуги (favorites).

Позволява на потребителите да:
- Добавят услуга към любими
- Премахват услуга от любими
- Преглеждат списък с любими услуги
"""
from flask import Blueprint, request, jsonify, Response
from db import db
from models.favorite import Favorite
from models.service import Service
from models.user import RegisteredUser

favorites_bp = Blueprint('favorites', __name__)


@favorites_bp.route('', methods=['GET'])
def get_favorites() -> tuple[Response, int]:
    """
    Връща любимите услуги на текущия потребител.

    Очаква header: X-User-ID
    """
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({'error': 'Не сте влезли в системата'}), 401

    user = db.session.get(RegisteredUser, int(user_id))
    if not user:
        return jsonify({'error': 'Потребителят не съществува'}), 404

    favorites = Favorite.query.filter_by(user_id=int(user_id)).all()

    # Използваме list comprehension за преобразуване
    result = [f.to_dict() for f in favorites]

    return jsonify(result), 200


@favorites_bp.route('', methods=['POST'])
def add_favorite() -> tuple[Response, int]:
    """
    Добавя услуга към любими.

    Очаква header: X-User-ID
    Очаква JSON: service_id
    """
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({'error': 'Не сте влезли в системата'}), 401

    user = db.session.get(RegisteredUser, int(user_id))
    if not user:
        return jsonify({'error': 'Потребителят не съществува'}), 404

    data = request.get_json()
    if not data or 'service_id' not in data:
        return jsonify({'error': 'Липсва service_id'}), 400

    service_id = data['service_id']

    # Проверяваме дали услугата съществува
    service = db.session.get(Service, service_id)
    if not service:
        return jsonify({'error': 'Услугата не съществува'}), 404

    # Проверяваме дали вече е добавена
    existing = Favorite.query.filter_by(
        user_id=int(user_id),
        service_id=service_id
    ).first()

    if existing:
        return jsonify({'error': 'Услугата вече е в любими'}), 400

    # Създаваме нов запис
    favorite = Favorite(user_id=int(user_id), service_id=service_id)
    db.session.add(favorite)
    db.session.commit()

    return jsonify({
        'message': 'Услугата е добавена към любими',
        'favorite': favorite.to_dict()
    }), 201


@favorites_bp.route('/<int:service_id>', methods=['DELETE'])
def remove_favorite(service_id: int) -> tuple[Response, int]:
    """
    Премахва услуга от любими.

    Очаква header: X-User-ID
    URL параметър: service_id
    """
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({'error': 'Не сте влезли в системата'}), 401

    # Търсим записа
    favorite = Favorite.query.filter_by(
        user_id=int(user_id),
        service_id=service_id
    ).first()

    if not favorite:
        return jsonify({'error': 'Услугата не е в любими'}), 404

    db.session.delete(favorite)
    db.session.commit()

    return jsonify({'message': 'Услугата е премахната от любими'}), 200


@favorites_bp.route('/check/<int:service_id>', methods=['GET'])
def check_favorite(service_id: int) -> tuple[Response, int]:
    """
    Проверява дали услуга е в любими.

    Очаква header: X-User-ID
    URL параметър: service_id

    Връща:
        is_favorite: true/false
    """
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({'error': 'Не сте влезли в системата'}), 401

    favorite = Favorite.query.filter_by(
        user_id=int(user_id),
        service_id=service_id
    ).first()

    return jsonify({'is_favorite': favorite is not None}), 200
