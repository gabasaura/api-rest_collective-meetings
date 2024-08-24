from flask import Blueprint, jsonify

routes = Blueprint('routes', __name__)

@routes.route('/')
def hello():
    return jsonify({'message': 'Hello, welcome to the WeMeet app!'}), 200