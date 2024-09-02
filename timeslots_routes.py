#### Routes for Timeslot ####
from flask import Blueprint, jsonify, abort, request
from sqlalchemy.exc import SQLAlchemyError
from models import db, Timeslot
from rank import calculate_rankings
from datetime import datetime

# Definición del Blueprint para las rutas de Timeslot
timeslots_bp = Blueprint('timeslots', __name__)

@timeslots_bp.route('/timeslots', methods=['POST'])
def create_timeslot():
    data = request.json
    if not data:
        abort(400, 'Request must be JSON')

    required_fields = ['meeting_id', 'user_id', 'date', 'block']
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        abort(400, f'Missing required fields: {", ".join(missing_fields)}')

    # Asegúrate de que el bloque sea un valor válido
    if data['block'] not in [1, 2, 3]:
        abort(400, 'Invalid block value. Must be 1, 2, or 3.')

    try:
        new_timeslot = Timeslot(
            meeting_id=data['meeting_id'],
            user_id=data['user_id'],
            date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
            block=data['block'],
            available=data.get('available', True)
        )
        db.session.add(new_timeslot)
        db.session.commit()
        return jsonify(new_timeslot.serialize()), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        abort(500, f'Error creating timeslot: {str(e)}')

@timeslots_bp.route('/update_timeslot', methods=['POST'])
def update_timeslot():
    data = request.json
    if not data:
        abort(400, 'Request must be JSON')

    # Validar y obtener los datos del request
    user_id = data.get('user_id')
    meeting_id = data.get('meeting_id')
    date_str = data.get('date')
    block = data.get('block')
    available = data.get('available')

    if not all([user_id, meeting_id, date_str, block is not None, available is not None]):
        abort(400, 'All fields (user_id, meeting_id, date, block, available) must be provided')

    try:
        # Convertir la fecha a un objeto de tipo date
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Buscar el timeslot existente
        timeslot = Timeslot.query.filter_by(user_id=user_id, meeting_id=meeting_id, date=date_obj, block=block).first()

        if timeslot:
            # Actualizar la disponibilidad si el timeslot existe
            timeslot.available = available
        else:
            # Crear un nuevo timeslot si no existe
            timeslot = Timeslot(user_id=user_id, meeting_id=meeting_id, date=date_obj, block=block, available=available)
            db.session.add(timeslot)

        db.session.commit()

        # Calcular los rankings después de la actualización
        rankings = calculate_rankings(meeting_id)

        return jsonify(rankings)

    except SQLAlchemyError as e:
        db.session.rollback()
        abort(500, f'Error updating timeslot: {str(e)}')

@timeslots_bp.route('/meetings/<int:meeting_id>/timeslots/<int:timeslot_id>', methods=['GET'])
def get_timeslot_for_meeting(meeting_id, timeslot_id):
    try:
        # Obtener el timeslot por su ID y el ID de la reunión
        timeslot = Timeslot.query.filter_by(id=timeslot_id, meeting_id=meeting_id).first_or_404()
        return jsonify(timeslot.serialize())
    except SQLAlchemyError as e:
        abort(500, f'Error retrieving timeslot: {str(e)}')

@timeslots_bp.route('/timeslots/<int:meeting_id>/<int:timeslot_id>', methods=['DELETE'])
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
