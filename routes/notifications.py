"""Маршрути за известия."""
from flask import Blueprint, request, jsonify, Response
from db import db
from models.notification import Notification
from models.user import RegisteredUser

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('', methods=['GET'])
def get_notifications() -> tuple[Response, int]:
    """Връща известията на потребителя."""
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({'error': 'Не сте влезли в системата'}), 401

    unread_only = request.args.get('unread_only', '').lower() == 'true'

    query = Notification.query.filter_by(user_id=int(user_id))
    if unread_only:
        query = query.filter_by(is_read=False)

    notifications = query.order_by(Notification.created_at.desc()).all()
    unread_count = Notification.query.filter_by(
        user_id=int(user_id), is_read=False
    ).count()

    return jsonify({
        'notifications': [n.to_dict() for n in notifications],
        'unread_count': unread_count
    }), 200


@notifications_bp.route('/<int:notification_id>/read', methods=['PUT'])
def mark_as_read(notification_id: int) -> tuple[Response, int]:
    """Маркира известие като прочетено."""
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({'error': 'Не сте влезли в системата'}), 401

    notification = db.session.get(Notification, notification_id)
    if not notification:
        return jsonify({'error': 'Известието не е намерено'}), 404

    if notification.user_id != int(user_id):
        return jsonify({'error': 'Нямате достъп'}), 403

    notification.mark_as_read()
    db.session.commit()

    return jsonify({'message': 'Маркирано като прочетено'}), 200


@notifications_bp.route('/read-all', methods=['PUT'])
def mark_all_as_read() -> tuple[Response, int]:
    """Маркира всички известия като прочетени."""
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({'error': 'Не сте влезли в системата'}), 401

    Notification.query.filter_by(
        user_id=int(user_id), is_read=False
    ).update({'is_read': True})
    db.session.commit()

    return jsonify({'message': 'Всички са маркирани'}), 200
