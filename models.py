from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from utils import generate_random_color, generate_meeting_hash
from sqlalchemy import Integer, CheckConstraint

db = SQLAlchemy()

# Definición de la tabla de asociación de participación de invitados
guest_participation = db.Table('user_meeting',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('meeting_id', db.Integer, db.ForeignKey('meeting.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), nullable=False),
    db.Column('confirmed', db.Boolean, nullable=False, default=False),
    db.Column('color', db.String(7), nullable=False)  # Color asignado al usuario para la reunión
)

# Tabla de asociación entre User y Role
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id'), primary_key=True)
)

class User(db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    # Relación con roles
    roles = db.relationship('Role', secondary=user_roles, backref=db.backref('users', lazy='dynamic'))

    def __init__(self, name, email):
        self.name = name
        self.email = email

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'roles': [role.name for role in self.roles]
        }

class Role(db.Model):
    __tablename__ = 'role'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __init__(self, name):
        self.name = name

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name
        }

class Meeting(db.Model):
    __tablename__ = 'meeting'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    password_hash = db.Column(db.String(64), nullable=False)

    total_guests = db.Column(db.Integer, default=0)
    confirmed_guests = db.Column(db.Integer, default=0)

    # Relación con otros modelos
    timeslots = db.relationship('Timeslot', backref='meeting', lazy='joined')
    final_date = db.relationship('FinalDate', backref='meeting', uselist=False, lazy='joined')

    def __init__(self, title, description, creator_id, password_hash):
        self.title = title
        self.description = description
        self.creator_id = creator_id
        self.password_hash = password_hash

    def serialize(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'creator_id': self.creator_id,
            'created_at': self.created_at.isoformat(),
            'timeslots': [t.serialize() for t in self.timeslots],
            'final_date': self.final_date.serialize() if self.final_date else None,
            'password_hash': self.password_hash,
            'total_guests': self.total_guests,
            'confirmed_guests': self.confirmed_guests
        }

class Timeslot(db.Model):
    __tablename__ = 'timeslot'

    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meeting.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    block = db.Column(Integer, nullable=False)
    available = db.Column(db.Boolean, nullable=False, default=True)

        # Agregar una restricción para validar los valores permitidos
    __table_args__ = (
        CheckConstraint('block in (1, 2, 3)', name='check_block_valid'),
    )

    def serialize(self):
        return {
            'id': self.id,
            'meeting_id': self.meeting_id,
            'user_id': self.user_id,
            'date': self.date.isoformat(),
            'block': self.block,
            'available': self.available
        }

class FinalDate(db.Model):
    __tablename__ = 'final_date'
    
    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meeting.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    confirmed_participants = db.Column(db.Integer, default=0)

    def serialize(self):
        return {
            'id': self.id,
            'meeting_id': self.meeting_id,
            'date': self.date.isoformat(),
            'confirmed_participants': self.confirmed_participants
        }
