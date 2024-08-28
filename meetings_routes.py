from flask import Blueprint, jsonify, request, abort
from sqlalchemy.exc import SQLAlchemyError
from models import db, User, Meeting, guest_participation, FinalDate, Role
from utils import generate_random_color, generate_meeting_hash

meetings_bp = Blueprint('meetings', __name__)

def validate_required_fields(data, required_fields):
    """Valida que los campos requeridos estén presentes en los datos proporcionados."""
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        abort(400, f'Missing required fields: {", ".join(missing_fields)}')

def get_or_create_role(role_name):
    """Obtiene un rol por nombre o lo crea si no existe."""
    role = Role.query.filter_by(name=role_name).first()
    if not role:
        role = Role(name=role_name)
        db.session.add(role)
        db.session.flush()  # Flushea para obtener el ID del rol
    return role

@meetings_bp.route('/meetings', methods=['POST'])
def create_meeting():
    data = request.json
    
    # Verificación de campos requeridos
    if not data:
        abort(400, 'Request must be JSON')
    validate_required_fields(data, ['title', 'creator_name', 'creator_email'])

    # Normalizar el correo electrónico del creador
    normalized_email = data['creator_email'].strip().lower()

    # Verificar si el usuario creador ya existe
    creator = User.query.filter_by(email=normalized_email).first()
    if creator:
        # Verificar si el usuario ya es creador en otra reunión
        if 'creator' in [role.name for role in creator.roles]:
            abort(400, 'This email is already used to create another meeting as a creator.')
    else:
        # Si el creador no existe, crearlo
        creator = User(name=data['creator_name'].strip(), email=normalized_email)
        db.session.add(creator)
        db.session.flush()  # Flushea para obtener el ID del creador

    try:
        # Generar un hash único para la reunión usando el título y el correo del creador
        meeting_hash = generate_meeting_hash(data['title'].strip(), normalized_email)

        # Crear la reunión
        new_meeting = Meeting(
            title=data['title'].strip(),
            description=data.get('description'),
            creator_id=creator.id,
            password_hash=meeting_hash
        )

        # Obtener o crear los roles de "moderator" y "creator"
        moderator_role = get_or_create_role('moderator')
        creator_role = get_or_create_role('creator')

        # Asignar los roles al creador
        if moderator_role not in creator.roles:
            creator.roles.append(moderator_role)
        if creator_role not in creator.roles:
            creator.roles.append(creator_role)

        db.session.add(new_meeting)
        db.session.commit()

        # Crear el enlace de invitación usando el hash generado
        invite_link = f"http://localhost:5000/meetings/{new_meeting.id}/access?hash={new_meeting.password_hash}"

        return jsonify({
            'message': 'Meeting created successfully',
            'meeting': new_meeting.serialize(),
            'invite_link': invite_link
        }), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        abort(500, f'Error creating meeting: {str(e)}') 

@meetings_bp.route('/meetings/<int:meeting_id>', methods=['DELETE'])
def delete_meeting(meeting_id):
    try:
        meeting = Meeting.query.get_or_404(meeting_id)

        # Opcional: Verificar dependencias antes de eliminar
        db.session.delete(meeting)
        db.session.commit()
        return jsonify({'message': 'Meeting deleted successfully'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        abort(500, f'Error deleting meeting: {str(e)}')

@meetings_bp.route('/meetings', methods=['GET'])
def get_all_meetings():
    meetings = Meeting.query.all()
    return jsonify([meeting.serialize() for meeting in meetings]), 200

@meetings_bp.route('/meetings/<int:meeting_id>', methods=['GET'])
def get_meeting_by_id(meeting_id):
    meeting = Meeting.query.get_or_404(meeting_id)
    return jsonify(meeting.serialize()), 200

@meetings_bp.route('/meetings/<int:meeting_id>/add_guest', methods=['POST'])
def add_guest_to_meeting(meeting_id):
    data = request.json
    if not data:
        abort(400, 'Request must be JSON')
    validate_required_fields(data, ['name', 'email'])

    normalized_email = data['email'].strip().lower()

    try:
        meeting = Meeting.query.get_or_404(meeting_id)

        # Verificar si el invitado ya existe para evitar duplicados
        existing_user = User.query.filter_by(email=normalized_email).first()
        if existing_user:
            abort(400, f'User with email {normalized_email} already exists.')

        # Crear nuevo usuario
        new_user = User(name=data['name'].strip(), email=normalized_email)
        db.session.add(new_user)
        db.session.flush()  # Flushea para obtener el ID del usuario

        # Obtener o crear el rol de "guest"
        guest_role = get_or_create_role('guest')

        # Añadir el nuevo invitado a la reunión
        color = generate_random_color()
        stmt = guest_participation.insert().values(
            user_id=new_user.id,
            meeting_id=meeting_id,
            role_id=guest_role.id,
            confirmed=False,
            color=color
        )
        db.session.execute(stmt)

        # Actualizar conteos de participantes
        meeting.total_guests += 1
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
        
        confirmed_guests = db.session.query(guest_participation).filter_by(meeting_id=meeting_id, confirmed=True).count()
        total_guests = db.session.query(guest_participation).filter_by(meeting_id=meeting_id).count()

        return jsonify({
            'meeting': meeting.title,
            'final_date': final_date.date.isoformat(),
            'total_guests': total_guests,
            'confirmed_guests': confirmed_guests
        }), 200

    except SQLAlchemyError as e:
        abort(500, f'Error retrieving meeting summary: {str(e)}')
