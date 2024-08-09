from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import random
import hashlib

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.Enum('creator', 'moderator', 'guest', name='role_enum'), nullable=False)
    color = db.Column(db.String(7), nullable=False, default=lambda: User._generate_random_color())
    active = db.Column(db.Boolean, nullable=False, default=True)

    meetings = db.relationship('Meeting', backref='creator', lazy=True)
    timeslots = db.relationship('Timeslot', backref='user', lazy=True)

    @staticmethod
    def _generate_random_color():
        excluded_colors = ['#FFFFFF', '#000000']
        color = None

        while not color or color in excluded_colors:
            color = "#{:06x}".format(random.randint(0, 0xFFFFFF))

        return color

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'color': self.color,
            'active': self.active
        }

class Meeting(db.Model):
    __tablename__ = 'meeting'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    password_hash = db.Column(db.String(64), nullable=False)

    timeslots = db.relationship('Timeslot', backref='meeting', lazy=True)
    final_date = db.relationship('FinalDate', backref='meeting', uselist=False, lazy=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.password_hash = self._generate_password_hash()

    def _generate_password_hash(self):
        # Generate a hash from the meeting title
        return hashlib.sha256(self.title.encode()).hexdigest()

    def serialize(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'creator_id': self.creator_id,
            'created_at': self.created_at.isoformat(),
            'timeslots': [t.serialize() for t in self.timeslots],
            'final_date': self.final_date.serialize() if self.final_date else None,
            'password_hash': self.password_hash
        }

class Timeslot(db.Model):
    __tablename__ = 'timeslot'

    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meeting.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    day = db.Column(db.Enum('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday', name='day_enum'), nullable=False)
    block = db.Column(db.Enum('Morning', 'Afternoon', 'Evening', name='block_enum'), nullable=False)
    available = db.Column(db.Boolean, nullable=False, default=True)

    def serialize(self):
        return {
            'id': self.id,
            'meeting_id': self.meeting_id,
            'user_id': self.user_id,
            'day': self.day,
            'block': self.block,
            'available': self.available
        }

class FinalDate(db.Model):
    __tablename__ = 'final_date'

    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meeting.id'), nullable=False)
    confirmed_date = db.Column(db.Date, nullable=False)
    confirmed_block = db.Column(db.Enum('Morning', 'Afternoon', 'Evening', name='block_enum'), nullable=False)

    def serialize(self):
        return {
            'id': self.id,
            'meeting_id': self.meeting_id,
            'confirmed_date': self.confirmed_date.isoformat(),
            'confirmed_block': self.confirmed_block
        }
