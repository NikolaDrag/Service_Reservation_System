from flask import Blueprint, request, jsonify, Response
from typing import Any
from datetime import datetime
from db import db
from models.reservation import Reservation, ReservationStatus
from models.service import Service
from models.user import RegisteredUser, Provider, UserRole

reservations_bp = Blueprint('reservations', __name__)


@reservations_bp.route('', methods=['GET'])
def get_reservations() -> tuple[Response, int]:
    """
    Връща резервации.
    
    Query параметри:
        user_id: Филтрира по клиент
        provider_id: Филтрира по доставчик
        status: Филтрира по статус
    """
    user_id = request.args.get('user_id', type=int)
    provider_id = request.args.get('provider_id', type=int)
    status_str = request.args.get('status')
    
    query = Reservation.query
    
    if user_id:
        query = query.filter_by(customer_id=user_id)
    if provider_id:
        query = query.filter_by(provider_id=provider_id)
    if status_str:
        try:
            status = ReservationStatus(status_str)
            query = query.filter_by(status=status)
        except ValueError:
            pass
    
    reservations = query.all()
    result = []
    for r in reservations:
        result.append({
            'id': r.id,
            'datetime': r.datetime.isoformat(),
            'status': r.status.value,
            'customer_id': r.customer_id,
            'provider_id': r.provider_id,
            'service_id': r.service_id,
            'notes': r.notes
        })
    
    return jsonify(result), 200


@reservations_bp.route('/<int:reservation_id>', methods=['GET'])
def get_reservation(reservation_id: int) -> tuple[Response, int]:
    reservation: Reservation | None = Reservation.query.get(reservation_id)
    
    if not reservation:
        return jsonify({'error': 'Резервацията не е намерена'}), 404
    
    return jsonify({
        'id': reservation.id,
        'datetime': reservation.datetime.isoformat(),
        'status': reservation.status.value,
        'customer_id': reservation.customer_id,
        'provider_id': reservation.provider_id,
        'service_id': reservation.service_id,
        'notes': reservation.notes
    }), 200


@reservations_bp.route('', methods=['POST'])
def create_reservation() -> tuple[Response, int]:
    """
    Създава нова резервация.
    
    Очаква header: X-User-ID
    Очаква JSON: datetime, service_id, notes (незадължително)
    """
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({'error': 'Не сте влезли в системата'}), 401
    
    user = RegisteredUser.query.get(int(user_id))
    if not user:
        return jsonify({'error': 'Потребителят не съществува'}), 404
    
    data: dict[str, Any] | None = request.get_json()
    if not data:
        return jsonify({'error': 'Липсват данни'}), 400
    
    if 'datetime' not in data or 'service_id' not in data:
        return jsonify({'error': 'Липсват задължителни полета (datetime, service_id)'}), 400
    
    try:
        # Използваме метода create_reservation от RegisteredUser
        reservation = user.create_reservation(
            service_id=data['service_id'],
            reservation_date=datetime.fromisoformat(data['datetime']),
            notes=data.get('notes')
        )
        return jsonify({'message': 'Резервацията е създадена', 'reservation_id': reservation.id}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@reservations_bp.route('/<int:reservation_id>', methods=['PUT'])
def update_reservation(reservation_id: int) -> tuple[Response, int]:
    reservation: Reservation | None = Reservation.query.get(reservation_id)
    
    if not reservation:
        return jsonify({'error': 'Резервацията не е намерена'}), 404
    
    data: dict[str, Any] | None = request.get_json()
    if not data:
        return jsonify({'error': 'Няма данни за обновяване'}), 400
    
    if 'datetime' in data:
        reservation.datetime = datetime.fromisoformat(data['datetime'])
    if 'notes' in data:
        reservation.notes = data['notes']
    
    db.session.commit()
    
    return jsonify({'message': 'Резервацията е обновена'}), 200


@reservations_bp.route('/<int:reservation_id>/status', methods=['PUT'])
def update_reservation_status(reservation_id: int) -> tuple[Response, int]:
    reservation: Reservation | None = Reservation.query.get(reservation_id)
    
    if not reservation:
        return jsonify({'error': 'Резервацията не е намерена'}), 404
    
    data: dict[str, Any] | None = request.get_json()
    if not data or 'status' not in data:
        return jsonify({'error': 'Липсва статус'}), 400
    
    valid_statuses = ['Pending', 'Confirmed', 'Canceled', 'Completed']
    if data['status'] not in valid_statuses:
        return jsonify({'error': f'Невалиден статус. Валидни: {valid_statuses}'}), 400
    
    reservation.status = ReservationStatus(data['status'])
    db.session.commit()
    
    return jsonify({'message': 'Статусът е обновен'}), 200


@reservations_bp.route('/<int:reservation_id>', methods=['DELETE'])
def delete_reservation(reservation_id: int) -> tuple[Response, int]:
    reservation: Reservation | None = Reservation.query.get(reservation_id)
    
    if not reservation:
        return jsonify({'error': 'Резервацията не е намерена'}), 404
    
    db.session.delete(reservation)
    db.session.commit()
    
    return jsonify({'message': 'Резервацията е изтрита'}), 200
