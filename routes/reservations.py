"""
Маршрути за резервации.

Включва:
- CRUD операции за резервации
- Свободни часове (available-slots)
- История на обслужвания
"""
from flask import Blueprint, request, jsonify, Response
from typing import Any
from datetime import datetime
from db import db
from models.reservation import Reservation, ReservationStatus
from models.service import Service
from models.user import RegisteredUser, Provider, UserRole

reservations_bp = Blueprint('reservations', __name__)


# ==================== СПЕЦИФИЧНИ МАРШРУТИ (ПРЕДИ WILDCARD) ====================

@reservations_bp.route('/available-slots', methods=['GET'])
def get_available_slots() -> tuple[Response, int]:
    """
    Връща свободните часове за даден ден и услуга.

    Query параметри:
        service_id: ID на услугата (задължително)
        date: Дата във формат YYYY-MM-DD (задължително)

    Връща:
        Списък с наличните часове за резервация
    """
    service_id = request.args.get('service_id', type=int)
    date_str = request.args.get('date')

    if not service_id or not date_str:
        return jsonify({'error': 'Липсват параметри (service_id, date)'}), 400

    service = db.session.get(Service, service_id)
    if not service:
        return jsonify({'error': 'Услугата не съществува'}), 404

    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Невалиден формат на датата. Използвайте YYYY-MM-DD'}), 400

    # Определяме работно време (по подразбиране 09:00 - 18:00)
    work_start = 9   # 09:00
    work_end = 18    # 18:00

    # Ако услугата има дефинирано работно време
    if service.working_hours_start and service.working_hours_end:
        work_start = service.working_hours_start.hour
        work_end = service.working_hours_end.hour

    # Продължителност на услугата (по подразбиране 60 минути)
    duration_minutes = service.duration or 60

    # Вземаме резервациите за този ден и услуга
    existing_reservations = Reservation.query.filter(
        Reservation.service_id == service_id,  # type: ignore[arg-type]
        db.func.date(Reservation.datetime) == target_date,  # type: ignore[arg-type]
        Reservation.status.in_([ReservationStatus.PENDING, ReservationStatus.CONFIRMED])  # type: ignore[attr-defined]
    ).all()

    # Създаваме set с заети часове (set comprehension)
    occupied_slots = {r.datetime.hour for r in existing_reservations}

    # Генерираме свободните часове (list comprehension)
    available_slots = [
        f"{hour:02d}:00"
        for hour in range(work_start, work_end)
        if hour not in occupied_slots
    ]

    return jsonify({
        'date': date_str,
        'service_id': service_id,
        'duration_minutes': duration_minutes,
        'available_slots': available_slots,
        'working_hours': f"{work_start:02d}:00 - {work_end:02d}:00"
    }), 200


@reservations_bp.route('/history', methods=['GET'])
def get_reservation_history() -> tuple[Response, int]:
    """
    Връща историята на обслужванията за потребител.

    Очаква header: X-User-ID
    Query параметри:
        role: 'customer' или 'provider' (по подразбиране 'customer')

    Връща:
        Списък с COMPLETED резервации
    """
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({'error': 'Не сте влезли в системата'}), 401

    role = request.args.get('role', 'customer')

    if role == 'provider':
        # История като сервиз
        reservations = Reservation.query.filter_by(
            provider_id=int(user_id),
            status=ReservationStatus.COMPLETED
        ).order_by(Reservation.datetime.desc()).all()
    else:
        # История като клиент
        reservations = Reservation.query.filter_by(
            customer_id=int(user_id),
            status=ReservationStatus.COMPLETED
        ).order_by(Reservation.datetime.desc()).all()

    # List comprehension за преобразуване
    result = [r.to_dict() for r in reservations]

    return jsonify({
        'history': result,
        'total_count': len(result)
    }), 200


# ==================== ОСНОВНИ CRUD МАРШРУТИ ====================

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

    # List comprehension за преобразуване на резервациите
    result = [
        {
            'id': r.id,
            'datetime': r.datetime.isoformat(),
            'status': r.status.value,
            'customer_id': r.customer_id,
            'provider_id': r.provider_id,
            'service_id': r.service_id,
            'notes': r.notes,
            'problem_image_url': r.problem_image_url
        }
        for r in reservations
    ]

    return jsonify(result), 200


@reservations_bp.route('', methods=['POST'])
def create_reservation() -> tuple[Response, int]:
    """
    Създава нова резервация.

    Очаква header: X-User-ID
    Очаква JSON: datetime, service_id, notes, problem_image_url (незадължително)
    """
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({'error': 'Не сте влезли в системата'}), 401

    user = db.session.get(RegisteredUser, int(user_id))
    if not user:
        return jsonify({'error': 'Потребителят не съществува'}), 404

    data: dict[str, Any] | None = request.get_json()
    if not data:
        return jsonify({'error': 'Липсват данни'}), 400

    if 'datetime' not in data or 'service_id' not in data:
        return jsonify({'error': 'Липсват задължителни полета (datetime, service_id)'}), 400

    try:
        reservation = user.create_reservation(
            service_id=data['service_id'],
            reservation_date=datetime.fromisoformat(data['datetime']),
            notes=data.get('notes'),
            problem_image_url=data.get('problem_image_url')
        )
        return jsonify({
            'message': 'Резервацията е създадена',
            'reservation_id': reservation.id
        }), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@reservations_bp.route('/<int:reservation_id>', methods=['GET'])
def get_reservation(reservation_id: int) -> tuple[Response, int]:
    """Връща конкретна резервация по ID."""
    reservation: Reservation | None = db.session.get(Reservation, reservation_id)

    if not reservation:
        return jsonify({'error': 'Резервацията не е намерена'}), 404

    return jsonify({
        'id': reservation.id,
        'datetime': reservation.datetime.isoformat(),
        'status': reservation.status.value,
        'customer_id': reservation.customer_id,
        'provider_id': reservation.provider_id,
        'service_id': reservation.service_id,
        'notes': reservation.notes,
        'problem_image_url': reservation.problem_image_url
    }), 200


@reservations_bp.route('/<int:reservation_id>', methods=['PUT'])
def update_reservation(reservation_id: int) -> tuple[Response, int]:
    """Обновява резервация."""
    reservation: Reservation | None = db.session.get(Reservation, reservation_id)

    if not reservation:
        return jsonify({'error': 'Резервацията не е намерена'}), 404

    data: dict[str, Any] | None = request.get_json()
    if not data:
        return jsonify({'error': 'Няма данни за обновяване'}), 400

    if 'datetime' in data:
        reservation.datetime = datetime.fromisoformat(data['datetime'])
    if 'notes' in data:
        reservation.notes = data['notes']
    if 'problem_image_url' in data:
        reservation.problem_image_url = data['problem_image_url']

    db.session.commit()

    return jsonify({'message': 'Резервацията е обновена'}), 200


@reservations_bp.route('/<int:reservation_id>/status', methods=['PUT'])
def update_reservation_status(reservation_id: int) -> tuple[Response, int]:
    """Обновява статуса на резервация."""
    reservation: Reservation | None = db.session.get(Reservation, reservation_id)

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
    """Изтрива резервация."""
    reservation: Reservation | None = db.session.get(Reservation, reservation_id)

    if not reservation:
        return jsonify({'error': 'Резервацията не е намерена'}), 404

    db.session.delete(reservation)
    db.session.commit()

    return jsonify({'message': 'Резервацията е изтрита'}), 200
