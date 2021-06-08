# Imports:
import os
import logging
import config
import flask

from flask import Flask, request, Response
from flask_restful import Api
from pymongo import MongoClient
from src.formatters import cursor_to_json, cursor_to_csv
from src.resources import DB_Fetch, DB_Access
from src.auth import hash_password, verify_password, build_auth_token, verify_auth_token


# Globals:
CONFIG = config.configuration()
app = Flask(__name__)
app.secret_key = os.urandom(24)
api = Api(app)

client = MongoClient('mongodb://{}'.format(os.environ['MONGODB_HOSTNAME']), 27017)
db = client['acp-brevets-app']
controles = db.controles
users = db.users

FORMATTERS = {
    'json': cursor_to_json,
    'csv': cursor_to_csv
}


# Resources:

@api.resource('/controles/<string:uid>', '/controles', resource_class_kwargs = {
    'app': app,
    'target_db': controles,
    'projection': {'_id': False},
    'sort_key': 'km'
})
class DB_Access_Generic(DB_Access):
    pass

@api.resource('/listAll/<string:ret_format>', '/listAll', resource_class_kwargs = {
    'app': app,
    'target_db': controles,
    'projection': {'_id': False, 'open': True, 'close': True},
    'formatters': FORMATTERS,
    'default_format': 'json',
    'sort_key': 'km'
})
class DB_Fetch_All(DB_Fetch):
    pass

@api.resource('/listOpenOnly/<string:ret_format>', '/listOpenOnly', resource_class_kwargs = {
    'app': app,
    'target_db': controles,
    'projection': {'_id': False, 'open': True},
    'formatters': FORMATTERS,
    'default_format': 'json',
    'sort_key': 'open'
})
class DB_Fetch_Open(DB_Fetch):
    pass

@api.resource('/listCloseOnly/<string:ret_format>', '/listCloseOnly/', resource_class_kwargs = {
    'app': app,
    'target_db': controles,
    'projection': {'_id': False, 'close': True},
    'formatters': FORMATTERS,
    'default_format': 'json',
    'sort_key': 'close'
})
class DB_Fetch_Close(DB_Fetch):
    pass

# Register a new user with this API.
@app.route('/register', methods=['POST'])
def register():
    app.logger.debug('Recieved user register request')
    username = request.form.get('username', '', type=str)
    password = request.form.get('password', '', type=str)

    if len(password) <= 0:
        app.logger.debug('\tPassword was too short')
        return Response('Password is too short.', 400)

    user = users.find_one({'username': username})
    if not user is None:
        app.logger.debug('\tCollided with preexisting user')
        return Response('That username already exists.', 400)

    pass_hash = hash_password(password)
    user_id = users.insert_one({'username': username, 'password': pass_hash}).inserted_id
    user_data = users.find_one({'_id': user_id})
    user_data['_id'] = '{}'.format(user_id)
    return flask.jsonify(user_data), 201

# Generate a token from this API.
@app.route('/token', methods=['GET'])
def token():
    app.logger.debug('Recieved user token request')
    username = request.args.get('username', '', type=str)
    password = request.args.get('password', '', type=str)

    user = users.find_one({'username': username})
    if user is None:
        app.logger.debug('\tNo such user exists')
        return Response('No such user exists', 401)

    pass_hash = user.get('password', None)
    if pass_hash is None:
        app.logger.debug('\tEncountered incorrectly formatted user')
        return Response('Invalid user format', 401)
    if not verify_password(password, pass_hash):
        app.logger.debug('\tPassword was invalid')
        return Response('Invalid password', 401)

    duration = 600
    token = build_auth_token({'id': f'{user["_id"]}', 'username': user['username']}, duration, app.secret_key)
    app.logger.debug('\tTOKEN: {}\n\tTYPE: {}'.format(token, type(token)))
    return flask.jsonify({'token': token, 'duration': duration}), 200

@app.route('/users/token/<string:token>')
def token_data(token):
    authorized, data = verify_auth_token(token, app.secret_key)
    if not authorized:
        return Response(data, 401)
    return flask.jsonify(data), 200


# Run:
app.debug = CONFIG.DEBUG
if app.debug:
    app.logger.setLevel(logging.DEBUG)

if __name__ == "__main__":
    app.logger.debug('Starting RESTful API at PORT {}'.format(CONFIG.PORT))
    app.run(port=int(CONFIG.PORT), host='0.0.0.0')

