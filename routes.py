from flask import Blueprint, jsonify, request, abort
from sqlalchemy.exc import SQLAlchemyError
from models import db, User, Meeting, Timeslot, FinalDate, guest_participation
import hashlib

routes = Blueprint('routes', __name__)

@routes.route('/')
def hello():
    return jsonify({'message': 'Hello, welcome to the WeMeet app!'}), 200

# Routes for User
@routes.route('/users', methods=['POST'])
def create_user():
    data = request.json
    if not data:
        abort(400, 'Request must be JSON')

    # Validar los campos requeridos
    required_fields = ['name', 'email']
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        abort(400, f'Missing required fields: {", ".join(missing_fields)}')

    try:
        # Crear un nuevo usuario con rol de invitado por defecto
        new_user = User(
            name=data['name'],
            email=data['email'],
        )
        db.session.add(new_user)
        db.session.commit()
        return jsonify(new_user.serialize()), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        abort(500, f'Error creating user: {str(e)}')

@routes.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        return jsonify(user.serialize())
    except SQLAlchemyError as e:
        abort(500, f'Error retrieving user: {str(e)}')

@routes.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        abort(500, f'Error deleting user: {str(e)}')


# Routes for Meeting
@routes.route('/meetings', methods=['POST'])
def create_meeting():
    data = request.json
    if not data:
        abort(400, 'Request must be JSON')

    # Validar los campos requeridos
    required_fields = ['title', 'creator_id']
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        abort(400, f'Missing required fields: {", ".join(missing_fields)}')

    try:
        # Crear una nueva reunión
        new_meeting = Meeting(
            title=data['title'],
            description=data.get('description'),
            creator_id=data['creator_id']
        )
        db.session.add(new_meeting)

        # Asignar roles al creador de la reunión: 'creator', 'moderator', y 'guest'
        creator = User.query.get_or_404(data['creator_id'])
        creator.role = 'creator'  # Actualiza el rol del creador a 'creator'

        # Establecer la relación en la tabla de asociación con el rol de moderador y confirmación
        stmt = guest_participation.insert().values(
            user_id=creator.id,
            meeting_id=new_meeting.id,
            confirmed=True  # El creador automáticamente confirma su participación
        )
        db.session.execute(stmt)

        db.session.commit()
        return jsonify(new_meeting.serialize()), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        abort(500, f'Error creating meeting: {str(e)}')

@routes.route('/meetings/<int:meeting_id>', methods=['GET'])
def get_meeting(meeting_id):
    try:
        meeting = Meeting.query.get_or_404(meeting_id)
        return jsonify(meeting.serialize())
    except SQLAlchemyError as e:
        abort(500, f'Error retrieving meeting: {str(e)}')

@routes.route('/meetings/<int:meeting_id>', methods=['DELETE'])
def delete_meeting(meeting_id):
    try:
        meeting = Meeting.query.get_or_404(meeting_id)
        db.session.delete(meeting)
        db.session.commit()
        return jsonify({'message': 'Meeting deleted successfully'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        abort(500, f'Error deleting meeting: {str(e)}')

@routes.route('/meetings/<int:meeting_id>/access', methods=['POST'])
def access_meeting(meeting_id):
    data = request.json
    if not data or not data.get('password'):
        abort(400, 'Password required')

    try:
        meeting = Meeting.query.get_or_404(meeting_id)
        hashed_password = hashlib.sha256(data['password'].encode()).hexdigest()

        if hashed_password == meeting.password_hash:
            return jsonify({'message': 'Access granted'}), 200
        else:
            abort(403, 'Invalid password')

    except SQLAlchemyError as e:
        abort(500, f'Error accessing meeting: {str(e)}')


# Routes for Timeslot
@routes.route('/timeslots', methods=['POST'])
def create_timeslot():
    data = request.json
    if not data:
        abort(400, 'Request must be JSON')

    # Validar los campos requeridos
    required_fields = ['meeting_id', 'user_id', 'day', 'block']
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        abort(400, f'Missing required fields: {", ".join(missing_fields)}')

    try:
        # Crear un nuevo timeslot
        new_timeslot = Timeslot(
            meeting_id=data['meeting_id'],
            user_id=data['user_id'],
            day=data['day'],
            block=data['block'],
            available=data.get('available', True)  # Default value is True
        )
        db.session.add(new_timeslot)
        db.session.commit()
        return jsonify(new_timeslot.serialize()), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        abort(500, f'Error creating timeslot: {str(e)}')

@routes.route('/timeslots/<int:timeslot_id>', methods=['GET'])
def get_timeslot(timeslot_id):
    try:
        timeslot = Timeslot.query.get_or_404(timeslot_id)
        return jsonify(timeslot.serialize())
    except SQLAlchemyError as e:
        abort(500, f'Error retrieving timeslot: {str(e)}')

@routes.route('/timeslots/<int:timeslot_id>', methods=['DELETE'])
def delete_timeslot(timeslot_id):
    try:
        timeslot = Timeslot.query.get_or_404(timeslot_id)
        db.session.delete(timeslot)
        db.session.commit()
        return jsonify({'message': 'Timeslot deleted successfully'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        abort(500, f'Error deleting timeslot: {str(e)}')


# Routes for FinalDate
@routes.route('/final_dates', methods=['POST'])
def create_final_date():
    data = request.json
    if not data:
        abort(400, 'Request must be JSON')

    # Validar los campos requeridos
    required_fields = ['meeting_id', 'confirmed_date', 'confirmed_block']
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        abort(400, f'Missing required fields: {", ".join(missing_fields)}')

    try:
        # Crear la fecha final de la reunión
        new_final_date = FinalDate(
            meeting_id=data['meeting_id'],
            confirmed_date=data['confirmed_date'],
            confirmed_block=data['confirmed_block']
        )
        db.session.add(new_final_date)
        db.session.commit()
        return jsonify(new_final_date.serialize()), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        abort(500, f'Error creating final date: {str(e)}')

@routes.route('/final_dates/<int:final_date_id>', methods=['GET'])
def get_final_date(final_date_id):
    try:
        final_date = FinalDate.query.get_or_404(final_date_id)
        return jsonify(final_date.serialize())
    except SQLAlchemyError as e:
        abort(500, f'Error retrieving final date: {str(e)}')

@routes.route('/final_dates/<int:final_date_id>', methods=['DELETE'])
def delete_final_date(final_date_id):
    try:
        final_date = FinalDate.query.get_or_404(final_date_id)
        db.session.delete(final_date)
        db.session.commit()
        return jsonify({'message': 'Final date deleted successfully'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        abort(500, f'Error deleting final date: {str(e)}')

