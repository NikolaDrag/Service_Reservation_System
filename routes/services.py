from flask import Blueprint, request, jsonify, Response
from typing import Any
from db import db
from models.service import Service
from models.user import User, UserRole

services_bp = Blueprint('services', __name__)


@services_bp.route('', methods=['GET'])
def get_all_services() -> tuple[Response, int]:
    services = Service.query.all()
    result = []
    for s in services:
        result.append({
            'id': s.id,
            'name': s.name,
            'description': s.description,
            'category': s.category,
            'provider_id': s.provider_id,
            'image_url': s.image_url
        })
    return jsonify(result), 200


@services_bp.route('/<int:service_id>', methods=['GET'])
def get_service(service_id: int) -> tuple[Response, int]:
    service: Service | None = Service.query.get(service_id)
    
    if not service:
        return jsonify({'error': 'Услугата не е намерена'}), 404
    
    return jsonify({
        'id': service.id,
        'name': service.name,
        'description': service.description,
        'category': service.category,
        'provider_id': service.provider_id,
        'working_hours_start': str(service.working_hours_start) if service.working_hours_start else None,
        'working_hours_end': str(service.working_hours_end) if service.working_hours_end else None,
        'image_url': service.image_url
    }), 200


@services_bp.route('', methods=['POST'])
def create_service() -> tuple[Response, int]:
    data: dict[str, Any] | None = request.get_json()
    
    if not data or not data.get('name') or not data.get('category') or not data.get('provider_id'):
        return jsonify({'error': 'Липсват задължителни полета'}), 400
    
    provider: User | None = User.query.get(data['provider_id'])
    if not provider or provider.role not in [UserRole.PROVIDER, UserRole.ADMIN]:
        return jsonify({'error': 'Невалиден доставчик'}), 400
    
    service = Service(
        name=data['name'],
        description=data.get('description'),
        category=data['category'],
        provider_id=data['provider_id'],
        image_url=data.get('image_url')
    )
    
    db.session.add(service)
    db.session.commit()
    
    return jsonify({'message': 'Услугата е създадена', 'service_id': service.id}), 201


@services_bp.route('/<int:service_id>', methods=['PUT'])
def update_service(service_id: int) -> tuple[Response, int]:
    service: Service | None = Service.query.get(service_id)
    
    if not service:
        return jsonify({'error': 'Услугата не е намерена'}), 404
    
    data: dict[str, Any] | None = request.get_json()
    if not data:
        return jsonify({'error': 'Няма данни за обновяване'}), 400
    
    if 'name' in data:
        service.name = data['name']
    if 'description' in data:
        service.description = data['description']
    if 'category' in data:
        service.category = data['category']
    if 'image_url' in data:
        service.image_url = data['image_url']
    
    db.session.commit()
    
    return jsonify({'message': 'Услугата е обновена'}), 200


@services_bp.route('/<int:service_id>', methods=['DELETE'])
def delete_service(service_id: int) -> tuple[Response, int]:
    service: Service | None = Service.query.get(service_id)
    
    if not service:
        return jsonify({'error': 'Услугата не е намерена'}), 404
    
    db.session.delete(service)
    db.session.commit()
    
    return jsonify({'message': 'Услугата е изтрита'}), 200


@services_bp.route('/search', methods=['GET'])
def search_services() -> tuple[Response, int]:
    name = request.args.get('name', '')
    category = request.args.get('category', '')
    
    query = Service.query
    
    if name:
        query = query.filter(Service.name.ilike(f'%{name}%'))
    if category:
        query = query.filter(Service.category.ilike(f'%{category}%'))
    
    services = query.all()
    result = []
    for s in services:
        result.append({
            'id': s.id,
            'name': s.name,
            'description': s.description,
            'category': s.category,
            'provider_id': s.provider_id
        })
    
    return jsonify(result), 200
