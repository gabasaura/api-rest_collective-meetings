#### Routes for Meeting ####
from flask import Blueprint, jsonify, request, abort
from sqlalchemy.exc import SQLAlchemyError
from models import db, User, Meeting, guest_participation, FinalDate
from utils import generate_random_color

meetings_bp = Blueprint('meetings', __name__)


@meetings_bp.route('/meetings', methods=['POST'])
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

@meetings_bp.route('/meetings/<int:meeting_id>', methods=['GET'])
def get_meeting(meeting_id):
    try:
        meeting = Meeting.query.get_or_404(meeting_id)
        return jsonify(meeting.serialize())
    except SQLAlchemyError as e:
        abort(500, f'Error retrieving meeting: {str(e)}')

@meetings_bp.route('/meetings/<int:meeting_id>', methods=['DELETE'])
def delete_meeting(meeting_id):
    try:
        meeting = Meeting.query.get_or_404(meeting_id)
        db.session.delete(meeting)
        db.session.commit()
        return jsonify({'message': 'Meeting deleted successfully'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        abort(500, f'Error deleting meeting: {str(e)}')

@meetings_bp.route('/meetings/<int:meeting_id>/access/<string:hash>', methods=['GET'])
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


@meetings_bp.route('/meetings/<int:meeting_id>/add_guest', methods=['POST'])
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

@meetings_bp.route('/meetings/<int:meeting_id>/final_date/<int:final_date_id>/summary', methods=['GET'])
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