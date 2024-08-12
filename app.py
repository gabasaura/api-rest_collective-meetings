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

    return app


if __name__ == '__main__':
    app = create_app()
    app.run()
