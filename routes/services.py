from flask import Blueprint, request, jsonify, Response
from typing import Any
from datetime import date
from db import db
from models.service import Service
from models.user import RegisteredUser, Provider, UserRole, Guest

services_bp = Blueprint('services', __name__)


@services_bp.route('', methods=['GET'])
def get_all_services() -> tuple[Response, int]:
    """Връща всички услуги."""
    services = Service.query.all()
    result = [s.to_dict() for s in services]
    return jsonify(result), 200


@services_bp.route('/<int:service_id>', methods=['GET'])
def get_service(service_id: int) -> tuple[Response, int]:
    """Връща услуга по ID."""
    guest = Guest()
    service = guest.view_service(service_id)

    if not service:
        return jsonify({'error': 'Услугата не е намерена'}), 404

    return jsonify(service), 200


@services_bp.route('', methods=['POST'])
def create_service() -> tuple[Response, int]:
    """
    Създава нова услуга.

    Очаква header: X-User-ID (трябва да е Provider или Admin)
    """
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({'error': 'Не сте влезли в системата'}), 401

    user = db.session.get(RegisteredUser, int(user_id))
    if not user or user.role not in [UserRole.PROVIDER, UserRole.ADMIN]:
        return jsonify({'error': 'Нямате права да създавате услуги'}), 403

    data: dict[str, Any] | None = request.get_json()
    if not data or not data.get('name') or not data.get('category'):
        return jsonify({'error': 'Липсват задължителни полета (name, category)'}), 400

    provider = db.session.get(Provider, int(user_id))
    if not provider:
        service = Service(
            name=data['name'],
            category=data['category'],
            provider_id=int(user_id),
            description=data.get('description'),
            price=data.get('price', 0.0),
            duration=data.get('duration', 60),
            availability=data.get('availability'),
            image_url=data.get('image_url')
        )
        db.session.add(service)
        db.session.commit()
    else:
        service = provider.create_service(
            name=data['name'],
            description=data.get('description', ''),
            category=data['category'],
            price=data.get('price', 0.0),
            duration=data.get('duration', 60),
            availability=data.get('availability')
        )

    return jsonify({'message': 'Услугата е създадена', 'service_id': service.id}), 201


@services_bp.route('/<int:service_id>', methods=['PUT'])
def update_service(service_id: int) -> tuple[Response, int]:
    """Обновява услуга."""
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({'error': 'Не сте влезли в системата'}), 401

    user = db.session.get(RegisteredUser, int(user_id))
    if not user:
        return jsonify({'error': 'Потребителят не е намерен'}), 404

    data: dict[str, Any] | None = request.get_json()
    if not data:
        return jsonify({'error': 'Няма данни за обновяване'}), 400

    service = db.session.get(Service, service_id)
    if not service:
        return jsonify({'error': 'Услугата не е намерена'}), 404

    if service.provider_id != int(user_id) and user.role != UserRole.ADMIN:
        return jsonify({'error': 'Нямате права да редактирате тази услуга'}), 403

    if 'name' in data:
        service.name = data['name']
    if 'description' in data:
        service.description = data['description']
    if 'category' in data:
        service.category = data['category']
    if 'price' in data:
        service.price = data['price']
    if 'duration' in data:
        service.duration = data['duration']
    if 'availability' in data:
        service.availability = data['availability']
    if 'image_url' in data:
        service.image_url = data['image_url']

    db.session.commit()
    return jsonify({'message': 'Услугата е обновена'}), 200


@services_bp.route('/<int:service_id>', methods=['DELETE'])
def delete_service(service_id: int) -> tuple[Response, int]:
    """Изтрива услуга."""
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({'error': 'Не сте влезли в системата'}), 401

    user = db.session.get(RegisteredUser, int(user_id))
    if not user:
        return jsonify({'error': 'Потребителят не е намерен'}), 404

    service = db.session.get(Service, service_id)
    if not service:
        return jsonify({'error': 'Услугата не е намерена'}), 404

    if service.provider_id != int(user_id) and user.role != UserRole.ADMIN:
        return jsonify({'error': 'Нямате права да изтриете тази услуга'}), 403

    db.session.delete(service)
    db.session.commit()
    return jsonify({'message': 'Услугата е изтрита'}), 200


@services_bp.route('/search', methods=['GET'])
def search_services() -> tuple[Response, int]:
    """
    Търси услуги.

    Query параметри:
        name: Част от името
        category: Категория
        date: Дата (YYYY-MM-DD)
    """
    name = request.args.get('name')
    category = request.args.get('category')
    date_str = request.args.get('date')

    date_on = None
    if date_str:
        try:
            date_on = date.fromisoformat(date_str)
        except ValueError:
            return jsonify({'error': 'Невалиден формат на дата. Използвайте YYYY-MM-DD'}), 400

    guest = Guest()
    result = guest.search_services(name=name, category=category, date_on=date_on)

    return jsonify(result), 200


@services_bp.route('/<int:service_id>/reviews', methods=['GET'])
def get_service_reviews(service_id: int) -> tuple[Response, int]:
    """Връща ревютата за услуга."""
    guest = Guest()
    reviews = guest.view_reviews(service_id)
    return jsonify(reviews), 200
