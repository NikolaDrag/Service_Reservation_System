"""Маршрути за известия."""
from flask import Blueprint, request, jsonify, Response
from db import db
from models.user import RegisteredUser

notifications_bp = Blueprint('notifications', __name__)


def _get_current_user() -> RegisteredUser | None:
    """Помощна функция за взимане на текущия потребител."""
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return None
    return db.session.get(RegisteredUser, int(user_id))


@notifications_bp.route('', methods=['GET'])
def get_notifications() -> tuple[Response, int]:
    """Връща известията на потребителя."""
    user = _get_current_user()
    if not user:
        return jsonify({'error': 'Не сте влезли в системата'}), 401

    unread_only = request.args.get('unread_only', '').lower() == 'true'
    return jsonify(user.get_notifications(unread_only=unread_only)), 200


@notifications_bp.route('/<int:notification_id>/read', methods=['PUT'])
def mark_as_read(notification_id: int) -> tuple[Response, int]:
    """Маркира известие като прочетено."""
    user = _get_current_user()
    if not user:
        return jsonify({'error': 'Не сте влезли в системата'}), 401

    success = user.mark_notification_read(notification_id)
    if not success:
        return jsonify({'error': 'Известието не е намерено или нямате достъп'}), 404

    return jsonify({'message': 'Маркирано като прочетено'}), 200


@notifications_bp.route('/read-all', methods=['PUT'])
def mark_all_as_read() -> tuple[Response, int]:
    """Маркира всички известия като прочетени."""
    user = _get_current_user()
    if not user:
        return jsonify({'error': 'Не сте влезли в системата'}), 401

    count = user.mark_all_notifications_read()
    return jsonify({'message': f'Маркирани {count} известия'}), 200
