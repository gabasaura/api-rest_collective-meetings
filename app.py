import os
from flask import Flask
from flask_migrate import Migrate
from flask_cors import CORS
from models import db
from flask_swagger_ui import get_swaggerui_blueprint

def create_app():
    app = Flask(__name__)

    # Configuración de Swagger
    SWAGGER_URL = '/swagger'
    API_URL = '/static/swagger.yaml'
    swaggerui_blueprint = get_swaggerui_blueprint(SWAGGER_URL, API_URL, config={'app_name': "Shared Calendar API"})
    
    app.config['DEBUG'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wemeet.db'

    db.init_app(app)
    CORS(app)
    migrate = Migrate(app, db)

    # Register Swagger blueprint
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

    # Register routes
    from routes import routes
    app.register_blueprint(routes)

    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run()
