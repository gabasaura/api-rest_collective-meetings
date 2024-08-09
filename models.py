from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import random
import hashlib

# Initialize SQLAlchemy for database handling
db = SQLAlchemy()

# Association Table for Users and Meetings
# This table establishes a many-to-many relationship between Users and Meetings
# It also includes a 'confirmed' boolean to track if a guest has confirmed their participation in a meeting
guest_participation = db.Table('user_meeting',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),  # Reference to the User model
    db.Column('meeting_id', db.Integer, db.ForeignKey('meeting.id'), primary_key=True),  # Reference to the Meeting model
    db.Column('confirmed', db.Boolean, nullable=False, default=False)  # Boolean to track if the user has confirmed participation
)

class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)  # Unique identifier for each user
    name = db.Column(db.String(50), nullable=False)  # Name of the user, cannot be null
    email = db.Column(db.String(120), unique=True, nullable=False)  # User's email, must be unique and not null
    role = db.Column(db.Enum('creator', 'moderator', 'guest', name='role_enum'), nullable=False)  # User role: creator, moderator, or guest
    color = db.Column(db.String(7), nullable=False, default=lambda: User._generate_random_color())  # User's color code, randomly generated
    active = db.Column(db.Boolean, nullable=False, default=True)  # Indicates if the user account is active

    # Relationship for users associated with multiple meetings (only relevant for guests)
    meetings = db.relationship('Meeting', secondary=guest_participation, backref='guests', lazy='dynamic')
    
    # Relationship for timeslots related to a user
    timeslots = db.relationship('Timeslot', backref='user', lazy=True)

    @staticmethod
    def _generate_random_color():
        """
        Generate a random color hex code, excluding black and white.
        Ensures that the generated color is not #FFFFFF (white) or #000000 (black).
        """
        excluded_colors = ['#FFFFFF', '#000000']
        color = None

        while not color or color in excluded_colors:
            color = "#{:06x}".format(random.randint(0, 0xFFFFFF))

        return color

    def serialize(self):
        """
        Serialize the User instance to a dictionary.
        Converts the User object into a dictionary format, making it easier to send as JSON.
        """
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

    id = db.Column(db.Integer, primary_key=True)  # Unique identifier for each meeting
    title = db.Column(db.String(100), nullable=False)  # Title of the meeting, cannot be null
    description = db.Column(db.Text, nullable=True)  # Optional description for the meeting
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Reference to the creator (User)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)  # Timestamp for when the meeting was created
    password_hash = db.Column(db.String(64), nullable=False)  # Hashed password for the meeting

    # Relationship for timeslots related to a meeting
    timeslots = db.relationship('Timeslot', backref='meeting', lazy=True)
    
    # Relationship for the final date of the meeting (one-to-one relationship)
    final_date = db.relationship('FinalDate', backref='meeting', uselist=False, lazy=True)

    def __init__(self, **kwargs):
        """
        Initialize a new Meeting instance and generate a password hash.
        Automatically hashes the meeting title to create a unique password hash.
        """
        super().__init__(**kwargs)
        self.password_hash = self._generate_password_hash()

    def _generate_password_hash(self):
        """
        Generate a SHA-256 hash of the meeting title to be used as a password hash.
        Ensures that the meeting has a secure, unique password based on its title.
        """
        return hashlib.sha256(self.title.encode()).hexdigest()

    def serialize(self):
        """
        Serialize the Meeting instance to a dictionary.
        Converts the Meeting object into a dictionary format, making it easier to send as JSON.
        """
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'creator_id': self.creator_id,
            'created_at': self.created_at.isoformat(),
            'timeslots': [t.serialize() for t in self.timeslots],  # Serialize all associated timeslots
            'final_date': self.final_date.serialize() if self.final_date else None,  # Serialize the final date if it exists
            'password_hash': self.password_hash
        }

class Timeslot(db.Model):
    __tablename__ = 'timeslot'

    id = db.Column(db.Integer, primary_key=True)  # Unique identifier for each timeslot
    meeting_id = db.Column(db.Integer, db.ForeignKey('meeting.id'), nullable=False)  # Reference to the meeting
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Reference to the user
    day = db.Column(db.Enum('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday', name='day_enum'), nullable=False)  # Day of the week
    block = db.Column(db.Enum('Morning', 'Afternoon', 'Evening', name='block_enum'), nullable=False)  # Time block (morning, afternoon, evening)
    available = db.Column(db.Boolean, nullable=False, default=True)  # Availability of the timeslot

    def serialize(self):
        """
        Serialize the Timeslot instance to a dictionary.
        Converts the Timeslot object into a dictionary format, making it easier to send as JSON.
        """
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

    id = db.Column(db.Integer, primary_key=True)  # Unique identifier for the final date
    meeting_id = db.Column(db.Integer, db.ForeignKey('meeting.id'), nullable=False)  # Reference to the meeting
    confirmed_date = db.Column(db.Date, nullable=False)  # Confirmed date for the meeting
    confirmed_block = db.Column(db.Enum('Morning', 'Afternoon', 'Evening', name='block_enum'), nullable=False)  # Confirmed time block

    def serialize(self):
        """
        Serialize the FinalDate instance to a dictionary.
        Converts the FinalDate object into a dictionary format, making it easier to send as JSON.
        """
        return {
            'id': self.id,
            'meeting_id': self.meeting_id,
            'confirmed_date': self.confirmed_date.isoformat(),
            'confirmed_block': self.confirmed_block
        }
