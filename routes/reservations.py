from flask import Blueprint, request, jsonify, Response
from typing import Any
from datetime import datetime
from db import db
from models.reservation import Reservation, ReservationStatus
from models.service import Service
from models.user import RegisteredUser, Provider, UserRole

reservations_bp = Blueprint('reservations', __name__)

@reservations_bp.route('/available-slots', methods=['GET'])
def get_available_slots():
    service_id = request.args.get('service_id', type=int)
    date_str = request.args.get('date')
    if not service_id or not date_str:
        return jsonify({'error': 'Missing params'}), 400
    service = db.session.get(Service, service_id)
    if not service:
        return jsonify({'error': 'Service not found'}), 404
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    work_start, work_end = 9, 18
    if service.working_hours_start and service.working_hours_end:
        work_start = service.working_hours_start.hour
        work_end = service.working_hours_end.hour
    duration_minutes = service.duration or 60
    existing = Reservation.query.filter(
        Reservation.service_id == service_id,
        db.func.date(Reservation.datetime) == target_date,
        Reservation.status.in_([ReservationStatus.PENDING, ReservationStatus.CONFIRMED])
    ).all()
    occupied = {r.datetime.hour for r in existing}
    available = [f'{h:02d}:00' for h in range(work_start, work_end) if h not in occupied]
    return jsonify({'date': date_str, 'service_id': service_id, 'duration_minutes': duration_minutes, 'available_slots': available, 'working_hours': f'{work_start:02d}:00 - {work_end:02d}:00'}), 200

@reservations_bp.route('/history', methods=['GET'])
def get_reservation_history():
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    role = request.args.get('role', 'customer')
    if role == 'provider':
        reservations = Reservation.query.filter_by(provider_id=int(user_id), status=ReservationStatus.COMPLETED).order_by(Reservation.datetime.desc()).all()
    else:
        reservations = Reservation.query.filter_by(customer_id=int(user_id), status=ReservationStatus.COMPLETED).order_by(Reservation.datetime.desc()).all()
    result = [r.to_dict() for r in reservations]
    return jsonify({'history': result, 'total_count': len(result)}), 200

@reservations_bp.route('', methods=['GET'])
def get_reservations():
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
    result = [{'id': r.id, 'datetime': r.datetime.isoformat(), 'status': r.status.value, 'customer_id': r.customer_id, 'provider_id': r.provider_id, 'service_id': r.service_id, 'notes': r.notes, 'problem_image_url': r.problem_image_url} for r in reservations]
    return jsonify(result), 200

@reservations_bp.route('', methods=['POST'])
def create_reservation():
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401
    user = db.session.get(RegisteredUser, int(user_id))
    if not user:
        return jsonify({'error': 'User not found'}), 404
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data'}), 400
    if 'datetime' not in data or 'service_id' not in data:
        return jsonify({'error': 'Missing fields'}), 400
    try:
        reservation = user.create_reservation(service_id=data['service_id'], reservation_date=datetime.fromisoformat(data['datetime']), notes=data.get('notes'), problem_image_url=data.get('problem_image_url'))
        return jsonify({'message': 'Created', 'reservation_id': reservation.id}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@reservations_bp.route('/<int:reservation_id>', methods=['GET'])
def get_reservation(reservation_id):
    reservation = db.session.get(Reservation, reservation_id)
    if not reservation:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({'id': reservation.id, 'datetime': reservation.datetime.isoformat(), 'status': reservation.status.value, 'customer_id': reservation.customer_id, 'provider_id': reservation.provider_id, 'service_id': reservation.service_id, 'notes': reservation.notes, 'problem_image_url': reservation.problem_image_url}), 200

@reservations_bp.route('/<int:reservation_id>', methods=['PUT'])
def update_reservation(reservation_id):
    reservation = db.session.get(Reservation, reservation_id)
    if not reservation:
        return jsonify({'error': 'Not found'}), 404
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data'}), 400
    if 'datetime' in data:
        reservation.datetime = datetime.fromisoformat(data['datetime'])
    if 'notes' in data:
        reservation.notes = data['notes']
    if 'problem_image_url' in data:
        reservation.problem_image_url = data['problem_image_url']
    db.session.commit()
    return jsonify({'message': 'Updated'}), 200

@reservations_bp.route('/<int:reservation_id>/status', methods=['PUT'])
def update_reservation_status(reservation_id):
    reservation = db.session.get(Reservation, reservation_id)
    if not reservation:
        return jsonify({'error': 'Not found'}), 404
    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({'error': 'Missing status'}), 400
    valid = ['Pending', 'Confirmed', 'Canceled', 'Completed']
    if data['status'] not in valid:
        return jsonify({'error': f'Invalid status. Valid: {valid}'}), 400
    reservation.status = ReservationStatus(data['status'])
    db.session.commit()
    return jsonify({'message': 'Status updated'}), 200

@reservations_bp.route('/<int:reservation_id>', methods=['DELETE'])
def delete_reservation(reservation_id):
    reservation = db.session.get(Reservation, reservation_id)
    if not reservation:
        return jsonify({'error': 'Not found'}), 404
    db.session.delete(reservation)
    db.session.commit()
    return jsonify({'message': 'Deleted'}), 200
