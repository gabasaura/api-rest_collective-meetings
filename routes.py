from flask import Blueprint, jsonify, request, abort
from models import db, User, Meeting, Timeslot, FinalDate
import hashlib

routes = Blueprint('routes', __name__)

@routes.route('/')
def hello():
    return jsonify({'message': 'Hello, welcome to the WeMeet app!'}), 200

# Routes for User
@routes.route('/users', methods=['POST'])
def create_user():
    data = request.json
    print(f"Received data: {data}")  # Debug line
    if not data or not data.get('name') or not data.get('email') or not data.get('role'):
        abort(400, 'Missing required fields')
    
    new_user = User(
        name=data.get('name'),
        email=data.get('email'),
        role=data.get('role'),
        color=User._generate_random_color()
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify(new_user.serialize()), 201


@routes.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.serialize())

# Routes for Meeting
@routes.route('/meetings', methods=['POST'])
def create_meeting():
    data = request.json
    new_meeting = Meeting(
        title=data.get('title'),
        description=data.get('description'),
        creator_id=data.get('creator_id')
    )
    db.session.add(new_meeting)
    db.session.commit()
    return jsonify(new_meeting.serialize()), 201

@routes.route('/meetings/<int:meeting_id>', methods=['GET'])
def get_meeting(meeting_id):
    meeting = Meeting.query.get_or_404(meeting_id)
    return jsonify(meeting.serialize())

@routes.route('/meetings/<int:meeting_id>/access', methods=['POST'])
def access_meeting(meeting_id):
    data = request.json
    meeting = Meeting.query.get_or_404(meeting_id)
    password = data.get('password')

    if not password:
        abort(400, 'Password required')

    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    if hashed_password == meeting.password_hash:
        return jsonify({'message': 'Access granted'}), 200
    else:
        abort(403, 'Invalid password')

# Routes for Timeslot
@routes.route('/timeslots', methods=['POST'])
def create_timeslot():
    data = request.json
    new_timeslot = Timeslot(
        meeting_id=data.get('meeting_id'),
        user_id=data.get('user_id'),
        day=data.get('day'),
        block=data.get('block'),
        available=data.get('available')
    )
    db.session.add(new_timeslot)
    db.session.commit()
    return jsonify(new_timeslot.serialize()), 201

@routes.route('/timeslots/<int:timeslot_id>', methods=['GET'])
def get_timeslot(timeslot_id):
    timeslot = Timeslot.query.get_or_404(timeslot_id)
    return jsonify(timeslot.serialize())

# Routes for FinalDate
@routes.route('/final_dates', methods=['POST'])
def create_final_date():
    data = request.json
    new_final_date = FinalDate(
        meeting_id=data.get('meeting_id'),
        confirmed_date=data.get('confirmed_date'),
        confirmed_block=data.get('confirmed_block')
    )
    db.session.add(new_final_date)
    db.session.commit()
    return jsonify(new_final_date.serialize()), 201

@routes.route('/final_dates/<int:final_date_id>', methods=['GET'])
def get_final_date(final_date_id):
    final_date = FinalDate.query.get_or_404(final_date_id)
    return jsonify(final_date.serialize())
