import json
import flask
from flask import Flask, request, Response
from flask_restful import Resource
from bson.objectid import ObjectId
from src.auth import verify_auth_token

# Database access resource
# '/base/<ret_format:str>'
class DB_Fetch(Resource):
    def __init__(self, app: Flask, target_db, projection: dict = {'_id': False}, formatters: dict = {}, default_format: str = None, sort_key: str = None):
        super().__init__()
        
        if isinstance(projection, dict):
            projection['_id'] = False
        elif isinstance(projection, list):
            new_projection = {'_id': False}
            for key in projection:
                if key == '_id':
                    continue
                new_projection[key] = True
            projection = new_projection

        self.app = app
        self.target_db = target_db
        self.projection = projection
        self.formatters = formatters
        self.default_format = default_format
        self.sort_key = sort_key

    def get(self, ret_format: str = None):
        self.app.logger.debug('DB_Fetch handler recieved GET request')

        token = request.args.get('token', None, type=str)
        authorized, token_data = verify_auth_token(token, self.app.secret_key)
        if not authorized:
            return token_data, 401

        if ret_format is None:
            ret_format = self.default_format

        formatter = self.formatters.get(ret_format, None)
        if not callable(formatter):
            self.app.logger.debug('\tDB_Fetch handler does not support return format {}'.format(ret_format))
            return Response('Invalid return format.', 501) # Return format is not supported

        max_num = request.args.get('top', 0, type=int)
        cursor = self.target_db.find({'username': token_data['username']}, projection = self.projection, limit = max_num)
        if not self.sort_key is None:
            cursor = cursor.sort(self.sort_key, 1)

        return Response(formatter(cursor), 200)


# Database access resource
# '/base/<uid:str>'
class DB_Access(Resource):
    def __init__(self, app: Flask, target_db, projection: dict = {}, sort_key: str = None):
        super().__init__()

        projection['_id'] = False

        self.app = app
        self.target_db = target_db
        self.projection = projection
        self.sort_key = sort_key

    def get(self, uid: str = None):
        self.app.logger.debug('DB_Access handler recieved GET request')

        token = request.args.get('token', None, type=str)
        authorized, token_data = verify_auth_token(token, self.app.secret_key)
        if not authorized:
            return token_data, 401

        if uid is None or uid == 'all':
            result = self.target_db.find({'username': token_data['username']}, projection=self.projection)
            if not self.sort_key is None:
                result = result.sort(self.sort_key, 1)
            result = list(result)
        else:
            result = self.target_db.find_one({'_id': ObjectId(uid), 'username': token_data['username']}, self.projection)
        return Response(json.dumps(result), 200)

    def post(self, uid: str = None):
        self.app.logger.debug('DB_Access handler recieved POST request')

        token = request.form.get('token', None, type=str)
        authorized, token_data = verify_auth_token(token, self.app.secret_key)
        if not authorized:
            return token_data, 401

        to_insert = request.form.get('data', None, type=str)
        if to_insert is None:
            self.app.logger.debug('\tPOST request had no data')
            return Response('Empty POST request.', 400)

        json_data = json.loads(to_insert)
        if isinstance(json_data, list):
            username = token_data['username']
            result = []
            for thing_to_insert in json_data:
                thing_to_insert['username'] = username
                result.append(self._insert(thing_to_insert))
        elif isinstance(json_data, dict):
            json_data['username'] = token_data['username']
            result = self._insert(json_data, uid)
        else:
            self.app.logger.debug('\tJson data was malformatted')
            return Response('Malformatted JSON data.', 400)

        self.app.logger.debug('\tFinished handling POST Request: {}'.format(result))
        return json.dumps(result), 200

    def _insert(self, element: dict, uid: str = None):
        if not uid is None:
            element['_id'] = ObjectId(uid)

        collision = self.target_db.find_one(element)
        if collision is None:
            result = self.target_db.insert_one(element).inserted_id
        else:
            result = collision['_id']

        self.app.logger.debug('Got id: {} (Type: {})'.format(result, type(result)))
        return "{}".format(result)

