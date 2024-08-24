#### Routes for Timeslot ####
from flask import Blueprint, jsonify, abort, request
from sqlalchemy.exc import SQLAlchemyError
from models import db, Timeslot
from rank import calculate_rankings
import datetime

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

@timeslots_bp.route('/update_timeslot', methods=['POST'])
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

@timeslots_bp.route('/meetings/<int:meeting_id>/timeslots/<int:timeslot_id>', methods=['GET'])
def get_timeslot_for_meeting(meeting_id, timeslot_id):
    try:
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

