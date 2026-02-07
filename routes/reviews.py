from flask import Blueprint, request, jsonify, Response
from typing import Any
from db import db
from models.review import Review
from models.service import Service
from models.user import RegisteredUser

reviews_bp = Blueprint('reviews', __name__)


@reviews_bp.route('', methods=['GET'])
def get_reviews() -> tuple[Response, int]:
    """Връща ревюта."""
    service_id = request.args.get('service_id', type=int)
    user_id = request.args.get('user_id', type=int)
    
    query = Review.query
    
    if service_id:
        query = query.filter_by(service_id=service_id)
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    reviews = query.all()
    result = []
    for r in reviews:
        result.append({
            'id': r.id,
            'rating': r.rating,
            'comment': r.comment,
            'user_id': r.user_id,
            'service_id': r.service_id
        })
    
    return jsonify(result), 200


@reviews_bp.route('/<int:review_id>', methods=['GET'])
def get_review(review_id: int) -> tuple[Response, int]:
    review: Review | None = Review.query.get(review_id)
    
    if not review:
        return jsonify({'error': 'Ревюто не е намерено'}), 404
    
    return jsonify({
        'id': review.id,
        'rating': review.rating,
        'comment': review.comment,
        'user_id': review.user_id,
        'service_id': review.service_id
    }), 200


@reviews_bp.route('', methods=['POST'])
def create_review() -> tuple[Response, int]:
    """
    Създава ревю.
    
    Очаква header: X-User-ID
    Очаква JSON: rating, service_id, comment (незадължително)
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
    
    if 'rating' not in data or 'service_id' not in data:
        return jsonify({'error': 'Липсват задължителни полета (rating, service_id)'}), 400
    
    try:
        # Използваме RegisteredUser.leave_review()
        review = user.leave_review(
            service_id=data['service_id'],
            rating=data['rating'],
            comment=data.get('comment')
        )
        return jsonify({'message': 'Ревюто е създадено', 'review_id': review.id}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@reviews_bp.route('/<int:review_id>', methods=['DELETE'])
def delete_review(review_id: int) -> tuple[Response, int]:
    review: Review | None = Review.query.get(review_id)
    
    if not review:
        return jsonify({'error': 'Ревюто не е намерено'}), 404
    
    db.session.delete(review)
    db.session.commit()
    
    return jsonify({'message': 'Ревюто е изтрито'}), 200
