"""
Маршрути за известия (notifications).

Позволява на потребителите да:
- Преглеждат списък с известия
- Маркират известие като прочетено
- Маркират всички като прочетени
- Изтриват известие
"""
from flask import Blueprint, request, jsonify, Response
from db import db
from models.notification import Notification
from models.user import RegisteredUser

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('', methods=['GET'])
def get_notifications() -> tuple[Response, int]:
    """
    Връща известията на текущия потребител.

    Очаква header: X-User-ID
    Query параметри:
        unread_only: Само непрочетени (true/false)
        limit: Максимален брой резултати
    """
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({'error': 'Не сте влезли в системата'}), 401

    user = db.session.get(RegisteredUser, int(user_id))
    if not user:
        return jsonify({'error': 'Потребителят не съществува'}), 404

    # Започваме заявката
    query = Notification.query.filter_by(user_id=int(user_id))

    # Филтър за само непрочетени
    unread_only = request.args.get('unread_only', '').lower() == 'true'
    if unread_only:
        query = query.filter_by(is_read=False)

    # Сортираме по дата (най-нови първо)
    query = query.order_by(Notification.created_at.desc())

    # Лимит
    limit = request.args.get('limit', type=int)
    if limit:
        query = query.limit(limit)

    notifications = query.all()

    # List comprehension за преобразуване
    result = [n.to_dict() for n in notifications]

    # Добавяме брой непрочетени
    unread_count = Notification.query.filter_by(
        user_id=int(user_id),
        is_read=False
    ).count()

    return jsonify({
        'notifications': result,
        'unread_count': unread_count
    }), 200


@notifications_bp.route('/unread-count', methods=['GET'])
def get_unread_count() -> tuple[Response, int]:
    """
    Връща само броя на непрочетените известия.

    Очаква header: X-User-ID
    """
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({'error': 'Не сте влезли в системата'}), 401

    count = Notification.query.filter_by(
        user_id=int(user_id),
        is_read=False
    ).count()

    return jsonify({'unread_count': count}), 200


@notifications_bp.route('/<int:notification_id>/read', methods=['PUT'])
def mark_as_read(notification_id: int) -> tuple[Response, int]:
    """
    Маркира известие като прочетено.

    Очаква header: X-User-ID
    URL параметър: notification_id
    """
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({'error': 'Не сте влезли в системата'}), 401

    notification = db.session.get(Notification, notification_id)
    if not notification:
        return jsonify({'error': 'Известието не е намерено'}), 404

    # Проверяваме дали известието принадлежи на потребителя
    if notification.user_id != int(user_id):
        return jsonify({'error': 'Нямате достъп до това известие'}), 403

    notification.mark_as_read()
    db.session.commit()

    return jsonify({
        'message': 'Известието е маркирано като прочетено',
        'notification': notification.to_dict()
    }), 200


@notifications_bp.route('/read-all', methods=['PUT'])
def mark_all_as_read() -> tuple[Response, int]:
    """
    Маркира ВСИЧКИ известия като прочетени.

    Очаква header: X-User-ID
    """
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({'error': 'Не сте влезли в системата'}), 401

    # Обновяваме всички непрочетени
    updated = Notification.query.filter_by(
        user_id=int(user_id),
        is_read=False
    ).update({'is_read': True})

    db.session.commit()

    return jsonify({
        'message': f'{updated} известия са маркирани като прочетени'
    }), 200


@notifications_bp.route('/<int:notification_id>', methods=['DELETE'])
def delete_notification(notification_id: int) -> tuple[Response, int]:
    """
    Изтрива известие.

    Очаква header: X-User-ID
    URL параметър: notification_id
    """
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({'error': 'Не сте влезли в системата'}), 401

    notification = db.session.get(Notification, notification_id)
    if not notification:
        return jsonify({'error': 'Известието не е намерено'}), 404

    # Проверяваме дали известието принадлежи на потребителя
    if notification.user_id != int(user_id):
        return jsonify({'error': 'Нямате достъп до това известие'}), 403

    db.session.delete(notification)
    db.session.commit()

    return jsonify({'message': 'Известието е изтрито'}), 200
