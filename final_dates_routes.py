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
        # Convertir meeting_id a entero
        meeting_id = int(meeting_id)

        # Obtener todos los timeslots para la reunión específica
        timeslots = Timeslot.query.filter_by(meeting_id=meeting_id).all()

        # Extraer las fechas únicas de los timeslots
        unique_dates = list(set(timeslot.date for timeslot in timeslots))
        
        # Verificar si hay fechas disponibles antes de calcular
        if not unique_dates:
            return jsonify({'message': 'No available dates found'}), 404

        # Calcular la fecha final utilizando la función proporcionada
        final_date = calculate_final_date(unique_dates)

        if final_date:
            return jsonify({'final_date': final_date.isoformat()}), 200
        else:
            return jsonify({'message': 'No final date could be calculated'}), 404

    except ValueError:
        abort(400, 'Invalid Meeting ID')
    except SQLAlchemyError as e:
        abort(500, f'Error retrieving final dates: {str(e)}')

@final_dates_bp.route('/final_date/<int:final_date_id>/update_confirmed', methods=['POST'])
def update_confirmed_for_final_date(final_date_id):
    try:
        # Get the final date object or return 404 if not found
        final_date = FinalDate.query.get_or_404(final_date_id)
        
        # Count confirmed participants for the meeting associated with the final date
        confirmed_count = db.session.query(guest_participation).filter_by(
            meeting_id=final_date.meeting_id,
            confirmed=True
        ).count()

        # Update the confirmed participants count
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
        # Check for existing final date with the same details
        existing_final_date = FinalDate.query.filter_by(
            meeting_id=data['meeting_id'],
            confirmed_date=data['confirmed_date'],
            confirmed_block=data['confirmed_block']
        ).first()

        if existing_final_date:
            abort(400, 'A final date with these details already exists')

        # Create and add new final date to the database
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
