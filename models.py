from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from utils import generate_random_color, generate_password_hash

db = SQLAlchemy()

# Association Table for Users and Meetings
# Esta tabla establece una relación de muchos a muchos entre los usuarios y las reuniones
# Aquí se guarda el rol del usuario y si ha confirmado su participación
guest_participation = db.Table('user_meeting',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('meeting_id', db.Integer, db.ForeignKey('meeting.id'), primary_key=True),
    db.Column('role', db.Enum('moderator', 'guest', name='role_enum'), nullable=False, default='guest'),  # El rol está ligado a la reunión
    db.Column('confirmed', db.Boolean, nullable=False, default=False),
    db.Column('color', db.String(7), nullable=False)  # Color asignado al usuario para la reunión, sin valor por defecto
)

class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)

    # Relación para los usuarios asociados con múltiples reuniones (relevante para cualquier rol)
    meetings = db.relationship('Meeting', secondary=guest_participation, backref='participants', lazy='dynamic')
    
    # Relación para los timeslots relacionados con un usuario
    timeslots = db.relationship('Timeslot', backref='user', lazy=True)

    def serialize(self):
        """
        Serializa la instancia de User a un diccionario.
        """
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
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
    is_private = db.Column(db.Boolean, nullable=False, default=False)  # Indica si la reunión es privada

    # Relación para los timeslots relacionados con una reunión
    timeslots = db.relationship('Timeslot', backref='meeting', lazy=True)
    
    # Relación para la fecha final de la reunión (uno a uno)
    final_date = db.relationship('FinalDate', backref='meeting', uselist=False, lazy=True)

    def __init__(self, **kwargs):
        """
        Inicializa una nueva instancia de Meeting y genera un hash de contraseña.
        """
        super().__init__(**kwargs)
        self.password_hash = generate_password_hash(self.title)

    def assign_roles(self):
        """
        Asigna los roles al creador y a los demás participantes.
        El creador también es moderador por defecto.
        """
        # Asigna el rol de moderador al creador de la reunión
        creator_participation = guest_participation.insert().values(
            user_id=self.creator_id,
            meeting_id=self.id,
            role='moderator',
            color=generate_random_color()  # Asigna un color al creador
        )
        db.session.execute(creator_participation)
        db.session.commit()

    def serialize(self):
        """
        Serializa la instancia de Meeting a un diccionario.
        """
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'creator_id': self.creator_id,
            'created_at': self.created_at.isoformat(),
            'timeslots': [t.serialize() for t in self.timeslots],
            'final_date': self.final_date.serialize() if self.final_date else None,
            'password_hash': self.password_hash,
            'is_private': self.is_private  # Incluye la información sobre la privacidad de la reunión
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
        """
        Serializa la instancia de Timeslot a un diccionario.
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

    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meeting.id'), nullable=False)
    confirmed_date = db.Column(db.Date, nullable=False)
    confirmed_block = db.Column(db.Enum('Morning', 'Afternoon', 'Evening', name='block_enum'), nullable=False)

    def serialize(self):
        """
        Serializa la instancia de FinalDate a un diccionario.
        """
        return {
            'id': self.id,
            'meeting_id': self.meeting_id,
            'confirmed_date': self.confirmed_date.isoformat(),
            'confirmed_block': self.confirmed_block
        }
