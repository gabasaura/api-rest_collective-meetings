from models import db, Meeting, User, Role, guest_participation
from utils import generate_meeting_hash, generate_random_color

class MeetingService:
    @staticmethod
    def create_meeting(title, creator_email, creator_id, description=None):
        """
        Crea una nueva reunión y asigna un rol de moderador al creador.
        """
        password_hash = generate_meeting_hash(title, creator_email)
        new_meeting = Meeting(title=title, description=description, creator_id=creator_id, password_hash=password_hash)
        
        db.session.add(new_meeting)
        db.session.commit()
        
        MeetingService.assign_creator_role(new_meeting.id, creator_id)
        return new_meeting

    @staticmethod
    def assign_creator_role(meeting_id, user_id):
        """
        Asigna el rol de moderador al creador de la reunión.
        """
        moderator_role = Role.query.filter_by(name='moderator').first()
        
        creator_participation = guest_participation.insert().values(
            user_id=user_id,
            meeting_id=meeting_id,
            role_id=moderator_role.id,
            color=generate_random_color()
        )
        db.session.execute(creator_participation)
        db.session.commit()

    @staticmethod
    def update_guest_counts(meeting):
        """
        Actualiza los conteos de invitados y confirmaciones.
        """
        meeting.total_guests = db.session.query(guest_participation).filter_by(meeting_id=meeting.id).count()
        meeting.confirmed_guests = db.session.query(guest_participation).filter_by(meeting_id=meeting.id, confirmed=True).count()
        db.session.commit()

class UserService:
    @staticmethod
    def create_user(name, email):
        """
        Crea un nuevo usuario.
        """
        new_user = User(name=name, email=email)
        db.session.add(new_user)
        db.session.commit()
        return new_user

    @staticmethod
    def get_user_by_email(email):
        """
        Obtiene un usuario por su email.
        """
        return User.query.filter_by(email=email).first()
