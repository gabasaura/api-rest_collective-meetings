import os
from flask import Flask
from flask_migrate import Migrate
from flask_cors import CORS
from models import db

def create_app():
    app = Flask(__name__)
    app.config['DEBUG'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wemeet.db'

    db.init_app(app)
    CORS(app)
    migrate = Migrate(app, db)

    # Register routes
    from routes import routes
    app.register_blueprint(routes)

    with app.app_context():
        db.create_all()
        create_default_user()

    return app

def create_default_user():
    """Create a default master creator user if it does not already exist."""
    from models import User
    master_email = 'master_creator@example.com'
    if not User.query.filter_by(email=master_email).first():
        master_user = User(
            name='Master Creator',
            email=master_email,
            role='creator',
            color=User._generate_random_color(),
            active=True
        )
        db.session.add(master_user)
        db.session.commit()
        print(f"Default user {master_email} created.")

if __name__ == '__main__':
    app = create_app()
    app.run()
