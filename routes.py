from flask import Blueprint, jsonify, request, abort
from sqlalchemy.exc import SQLAlchemyError
from models import db, User, Meeting, Timeslot, FinalDate, guest_participation
from utils import generate_random_color, generate_password_hash
from rank import calculate_rankings
import datetime

import hashlib

routes = Blueprint('routes', __name__)

@routes.route('/')
def hello():
    return jsonify({'message': 'Hello, welcome to the WeMeet app!'}), 200

# Routes for User

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

    required_fields = ['title', 'creator_name', 'creator_email', 'is_private']
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        abort(400, f'Missing required fields: {", ".join(missing_fields)}')

    try:
        # Verificar si el usuario creador ya existe
        creator = User.query.filter_by(email=data['creator_email']).first()
        if not creator:
            # Si el creador no existe, crearlo
            creator = User(
                name=data['creator_name'],
                email=data['creator_email']
            )
            db.session.add(creator)
            db.session.flush()  # Obtener ID del creador

        # Crear la reunión
        new_meeting = Meeting(
            title=data['title'],
            description=data.get('description'),
            creator_id=creator.id,
            is_private=data['is_private']
        )
        db.session.add(new_meeting)
        db.session.flush()  # Obtener ID de la reunión

        # Asignar color y rol de moderador al creador
        creator_color = generate_random_color()
        stmt = guest_participation.insert().values(
            user_id=creator.id,
            meeting_id=new_meeting.id,
            role='moderator',
            confirmed=True,
            color=creator_color
        )
        db.session.execute(stmt)

        # Si la reunión es privada, generar un hash
        if new_meeting.is_private:
            meeting_hash = generate_password_hash(data['title'])
            new_meeting.password_hash = meeting_hash
            db.session.commit()

            invite_link = f"http://localhost:5000/meetings/{new_meeting.id}/access?hash={meeting_hash}"
            return jsonify({
                'message': 'Meeting created successfully',
                'meeting': new_meeting.serialize(),
                'invite_link': invite_link
            }), 201
        else:
            new_meeting.password_hash = None
            db.session.commit()
            return jsonify({
                'message': 'Meeting created successfully',
                'meeting': new_meeting.serialize()
            }), 201

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

@routes.route('/meetings/<int:meeting_id>/access/<string:hash>', methods=['GET'])
def access_meeting(meeting_id, hash):
    try:
        # Buscar la reunión por ID
        meeting = Meeting.query.get_or_404(meeting_id)

        # Verificar si la reunión es privada y si el hash coincide
        if meeting.is_private and hash != meeting.password_hash:
            abort(403, 'Invalid access hash')

        # Si todo es válido, conceder acceso
        return jsonify({'message': 'Access granted'}), 200

    except SQLAlchemyError as e:
        abort(500, f'Error accessing meeting: {str(e)}')


@routes.route('/meetings/<int:meeting_id>/add_guest', methods=['POST'])
def add_guest_to_meeting(meeting_id):
    data = request.json
    if not data:
        abort(400, 'Request must be JSON')

    required_fields = ['name', 'email']
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        abort(400, f'Missing required fields: {", ".join(missing_fields)}')

    try:
        meeting = Meeting.query.get_or_404(meeting_id)
        new_user = User(
            name=data['name'],
            email=data['email']
        )
        db.session.add(new_user)
        db.session.flush()

        color = generate_random_color()
        stmt = guest_participation.insert().values(
            user_id=new_user.id,
            meeting_id=meeting_id,
            role='guest',
            confirmed=False,
            color=color
        )
        db.session.execute(stmt)
        db.session.commit()

        # Update participant counts
        meeting.total_participants += 1
        db.session.commit()

        return jsonify({
            'message': f'User {new_user.name} added as guest to meeting {meeting.title}',
            'user': new_user.serialize(),
            'meeting': meeting.serialize(),
            'color': color
        }), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        abort(500, f'Error adding guest to meeting: {str(e)}')



# Routes for Timeslot

@routes.route('/timeslots', methods=['POST'])
def create_timeslot():
    data = request.json
    if not data:
        abort(400, 'Request must be JSON')

    required_fields = ['meeting_id', 'user_id', 'date', 'block']
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        abort(400, f'Missing required fields: {", ".join(missing_fields)}')

    try:
        new_timeslot = Timeslot(
            meeting_id=data['meeting_id'],
            user_id=data['user_id'],
            date=datetime.strptime(data['date'], '%Y-%m-%d').date(),  # Convertir la fecha a objeto date
            block=data['block'],
            available=data.get('available', True)
        )
        db.session.add(new_timeslot)
        db.session.commit()
        return jsonify(new_timeslot.serialize()), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        abort(500, f'Error creating timeslot: {str(e)}')

@routes.route('/update_timeslot', methods=['POST'])
def update_timeslot():
    data = request.json
    user_id = data.get('user_id')
    meeting_id = data.get('meeting_id')
    date = datetime.strptime(data.get('date'), '%Y-%m-%d').date()  # Convertir la fecha a objeto date
    block = data.get('block')
    available = data.get('available')

    timeslot = Timeslot.query.filter_by(user_id=user_id, meeting_id=meeting_id, date=date, block=block).first()
    if timeslot:
        timeslot.available = available
    else:
        timeslot = Timeslot(user_id=user_id, meeting_id=meeting_id, date=date, block=block, available=available)
        db.session.add(timeslot)

    db.session.commit()

    rankings = calculate_rankings(meeting_id)

    return jsonify(rankings)

@routes.route('/meetings/<int:meeting_id>/timeslots/<int:timeslot_id>', methods=['GET'])
def get_timeslot_for_meeting(meeting_id, timeslot_id):
    try:
        timeslot = Timeslot.query.filter_by(id=timeslot_id, meeting_id=meeting_id).first_or_404()
        return jsonify(timeslot.serialize())
    except SQLAlchemyError as e:
        abort(500, f'Error retrieving timeslot: {str(e)}')


@routes.route('/timeslots/<int:meeting_id>/<int:timeslot_id>', methods=['DELETE'])
def delete_timeslot(meeting_id, timeslot_id):
    try:
        # Filtrar el timeslot por meeting_id y timeslot_id
        timeslot = Timeslot.query.filter_by(id=timeslot_id, meeting_id=meeting_id).first_or_404()
        
        # Si se encuentra, se procede a eliminarlo
        db.session.delete(timeslot)
        db.session.commit()
        
        return jsonify({'message': 'Timeslot deleted successfully'}), 200
    except SQLAlchemyError as e:
        # Si hay un error durante la eliminación, se hace rollback y se devuelve un error
        db.session.rollback()
        abort(500, f'Error deleting timeslot: {str(e)}')


# Routes for FinalDate

@routes.route('/final_dates', methods=['POST'])
def create_final_date():
    data = request.json
    if not data:
        abort(400, 'Request must be JSON')

    required_fields = ['meeting_id', 'confirmed_date', 'confirmed_block']
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        abort(400, f'Missing required fields: {", ".join(missing_fields)}')

    try:
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


@routes.route('/final_dates', methods=['GET'])
def get_final_dates():
    meeting_id = request.args.get('meeting_id')
    if not meeting_id:
        abort(400, 'Meeting ID is required')

    try:
        # Suponiendo que `calculate_final_dates` es la función que genera el ranking final
        final_dates = calculate_final_dates(meeting_id)
        return jsonify(final_dates), 200
    except SQLAlchemyError as e:
        abort(500, f'Error retrieving final dates: {str(e)}')

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
