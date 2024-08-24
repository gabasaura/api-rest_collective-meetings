#### Routes for Users ####
from flask import Blueprint, jsonify, abort
from sqlalchemy.exc import SQLAlchemyError
from models import db, User

users_bp = Blueprint('users', __name__)

@users_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        return jsonify(user.serialize())
    except SQLAlchemyError as e:
        abort(500, f'Error retrieving user: {str(e)}')

@users_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        abort(500, f'Error deleting user: {str(e)}')