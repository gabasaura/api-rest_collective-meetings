#### final_dates_bp for Final Date ####
from flask import Blueprint, jsonify, abort, request
from sqlalchemy.exc import SQLAlchemyError
from models import db, Timeslot, FinalDate, guest_participation
from final_date import calculate_final_date

final_dates_bp = Blueprint('final_dates', __name__)

@final_dates_bp.route('/final_dates', methods=['GET'])
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

@final_dates_bp.route('/final_date/<int:final_date_id>/update_confirmed', methods=['POST'])
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

@final_dates_bp.route('/final_dates', methods=['POST'])
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