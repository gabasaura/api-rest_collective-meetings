from flask import Blueprint, jsonify, request, abort
from sqlalchemy.exc import SQLAlchemyError
from models import db, User, Meeting, Timeslot, FinalDate, guest_participation
from utils import generate_random_color
from rank import calculate_rankings
from final_date import calculate_final_date
import datetime

routes = Blueprint('routes', __name__)

@routes.route('/')
def hello():
    return jsonify({'message': 'Hello, welcome to the WeMeet app!'}), 200

#### Routes for Users ####

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

#### Routes for Meeting ####

@routes.route('/meetings', methods=['POST'])
def create_meeting():
    data = request.json
    
    # Verificación de campos requeridos
    if not data or 'title' not in data or 'creator_email' not in data:
        abort(400, 'Missing required fields')

    required_fields = ['title', 'creator_name', 'creator_email']
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        abort(400, f'Missing required fields: {", ".join(missing_fields)}')

    # Normalizar el correo electrónico del creador
    normalized_email = data['creator_email'].strip().lower()

    # Verificar si el correo del creador ya existe en otra reunión
    existing_meeting = Meeting.query.join(User).filter(
        User.email == normalized_email,
        Meeting.creator_id == User.id
    ).first()

    if existing_meeting:
        abort(400, 'This email is already used to create another meeting.')

    try:
        # Verificar si el usuario creador ya existe
        creator = User.query.filter_by(email=normalized_email).first()
        if not creator:
            # Si el creador no existe, crearlo
            creator = User(
                name=data['creator_name'].strip(),
                email=normalized_email
            )
            db.session.add(creator)
            db.session.flush()  # Flushea para obtener el ID del creador

        # Crear la reunión
        new_meeting = Meeting(
            title=data['title'].strip(),
            description=data.get('description'),
            creator_id=creator.id,
            creator_email=normalized_email  # Pasar creator_email para el hash en el constructor
        )
        db.session.add(new_meeting)
        db.session.commit()

        # Crear el enlace de invitación usando el hash que ya está en la instancia
        invite_link = f"http://localhost:5000/meetings/{new_meeting.id}/access?hash={new_meeting.password_hash}"

        return jsonify({
            'message': 'Meeting created successfully',
            'meeting': new_meeting.serialize(),
            'invite_link': invite_link
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
        db.session.flush()  # Flush to get new_user.id before committing

        # Add new guest to the meeting
        color = generate_random_color()
        stmt = guest_participation.insert().values(
            user_id=new_user.id,
            meeting_id=meeting_id,
            role='guest',
            confirmed=False,
            color=color
        )
        db.session.execute(stmt)

        # Update participant counts
        meeting.total_guests += 1  # Use total_guests instead of total_participants
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

@routes.route('/meetings/<int:meeting_id>/final_date/<int:final_date_id>/summary', methods=['GET'])
def get_meeting_summary(meeting_id, final_date_id):
    try:
        meeting = Meeting.query.get_or_404(meeting_id)
        final_date = FinalDate.query.get_or_404(final_date_id)
        
        confirmed_guests = meeting.count_confirmed_guests(final_date.date)
        total_guests = meeting.count_total_guests()

        return jsonify({
            'meeting': meeting.title,
            'final_date': final_date.date.isoformat(),
            'total_guests': total_guests,
            'confirmed_guests': confirmed_guests
        }), 200

    except SQLAlchemyError as e:
        abort(500, f'Error retrieving meeting summary: {str(e)}')


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


# Ruta para crear una nueva fecha final
@routes.route('/final_dates', methods=['GET'])
def get_final_dates():
    meeting_id = request.args.get('meeting_id')
    if not meeting_id:
        abort(400, 'Meeting ID is required')

    try:
        # Obtén todos los timeslots para la reunión específica
        timeslots = Timeslot.query.filter_by(meeting_id=meeting_id).all()
        final_date = calculate_final_date([timeslot.date for timeslot in timeslots])

        if final_date:
            return jsonify({'final_date': final_date}), 200
        else:
            return jsonify({'message': 'No available dates found'}), 404
    except SQLAlchemyError as e:
        abort(500, f'Error retrieving final dates: {str(e)}')

@routes.route('/final_date/<int:final_date_id>/update_confirmed', methods=['POST'])
def update_confirmed_for_final_date(final_date_id):
    try:
        final_date = FinalDate.query.get_or_404(final_date_id)
        
        confirmed_count = db.session.query(guest_participation).filter_by(
            meeting_id=final_date.meeting_id,
            confirmed=True
        ).count()

        final_date.confirmed_participants = confirmed_count
        db.session.commit()

        return jsonify({
            'message': f'Confirmed participants updated for final date {final_date.confirmed_date}',
            'final_date': final_date.serialize()
        }), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        abort(500, f'Error updating confirmed participants: {str(e)}')

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
        # Verifica si ya existe una fecha final con los mismos detalles
        existing_final_date = FinalDate.query.filter_by(
            meeting_id=data['meeting_id'],
            confirmed_date=data['confirmed_date'],
            confirmed_block=data['confirmed_block']
        ).first()

        if existing_final_date:
            abort(400, 'A final date with these details already exists')

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
