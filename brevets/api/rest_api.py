# Imports:
import os
import logging
import config
from flask import Flask
from flask_restful import Api
from pymongo import MongoClient
from src.formatters import cursor_to_json, cursor_to_csv
from src.resources import DB_Fetch, DB_Access


# Globals:
CONFIG = config.configuration()
app = Flask(__name__)
app.secret_key = os.urandom(24)
api = Api(app)

client = MongoClient('mongodb://{}'.format(os.environ['MONGODB_HOSTNAME']), 27017)
db = client['acp-brevets-app']
controles = db.controles

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


# Run:
app.debug = CONFIG.DEBUG
if app.debug:
    app.logger.setLevel(logging.DEBUG)

if __name__ == "__main__":
    app.logger.debug('Starting RESTful API at PORT {}'.format(CONFIG.PORT))
    app.run(port=int(CONFIG.PORT), host='0.0.0.0')

