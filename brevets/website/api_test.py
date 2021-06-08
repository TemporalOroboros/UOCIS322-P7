# Globals:
import os
import logging
import requests

import config
from datetime import timedelta
from json import loads
from flask import Flask, render_template, request, Response
from flask_login import LoginManager, current_user, login_required, login_user, logout_user, UserMixin, confirm_login, fresh_login_required
from flask_wtf import FlaskForm as Form
from wtforms import StringField, BooleanField, SelectField, validators

CONFIG = config.configuration()
app = Flask(__name__)
app.secret_key = os.urandom(24)
login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'login'
login_manager.login_message = u'Please log in to access this page'
login_manager.refresh_view = 'login'
login_manager.needs_refresh_message = u'To protect your account, please reauthenticate to access this page'
login_manager.init_app(app)

API_URL_BASE = 'http://{}:{}'.format(os.environ['RESTAPI_HOSTNAME'], os.environ['RESTAPI_PORT'])

class LoginForm(Form):
    username = StringField('Username', [
        validators.Length(min=2, max=25, message='The username is too short or too long!'),
        validators.InputRequired(u'A username is required to login or register an account!')
    ])
    password = StringField('Password', [
        validators.Length(min=2, max=25, message='The password is too short or too long!'),
        validators.InputRequired(u'A password is required to login or register an account!')
    ])
    remember = BooleanField('Remember me') 

class User(UserMixin):
    def __init__(self, token, username):

        self.id = token
        self.token = token
        self.username = username


##
# Pageserver
##

@app.route("/index")
@app.route("/")
def serve_index():
    app.logger.debug('Now serving index page')
    login_form = LoginForm()
    return render_template('api.html', login_form=login_form), 200

##
# API Interface
##


@login_manager.user_loader
def load_user(user_id):
    # Request user data from rest_api
    # User data is retrived via token
    query_result = requests.get('{}/users/token/{}'.format(API_URL_BASE, user_id))
    if query_result.status_code >= 300:
        return None

    user_data = loads(query_result.text)
    return User(user_id, user_data['username'])

@app.route('/register', methods=['POST'])
def register():
    if request.method != 'POST':
        return Response('Invalid method: {}'.format(request.method), 400)

    form = LoginForm()
    if not form.validate_on_submit():
        return Response('Invalid form.', 400)

    username = request.form.get('username', None, type=str)
    password = request.form.get('password', None, type=str)
    if username is None or password is None:
        return Response('Missing username or password.', 400)

    response_data = requests.post('{}/register'.format(API_URL_BASE), {'username': username, 'password': password})
    return Response(response_data.text, response_data.status_code) 

@app.route('/login', methods=['POST'])
def login():
    if request.method != 'POST':
        return Response('Wrong method: {}'.format(request.method), 400)

    form = LoginForm()
    if not form.validate_on_submit():
        return Response('Invalid form.', 400)

    username = request.form.get('username', None, type=str)
    password = request.form.get('password', None, type=str)
    remember = request.form.get('remember', 'false') == 'true'
    if username is None or password is None:
        return Response('Missing username or password.', 400)

    query_result = requests.get(f'{API_URL_BASE}/token', {'username': username, 'password': password})
    if query_result.status_code >= 300:
        return Response(query_result.text, query_result.status_code)

    query_data = loads(query_result.text)
    user = User(query_data['token'], username)
    if not login_user(user, remember=remember, duration=timedelta(seconds = int(query_data['duration']))):
        return Response('Failed login.', 401)
    return Response('Success!', 200)

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return Response('Success!', 200)


@app.route("/test_api/<string:url_path>/<string:ret_format>")
@fresh_login_required
def test_api_with_format(url_path: str, ret_format: str = ''):
    api_url = '{}/{}/{}'.format(API_URL_BASE, url_path, ret_format)

    query_data = {'token': current_user.token}
    limit = request.args.get('top', None, type=int)
    if not (limit is None or limit == ''):
        query_data['top'] = limit

    response_data = requests.get(api_url, query_data)
    return Response(response_data.text, response_data.status_code) 

@app.route("/test_api/<string:url_path>")
@fresh_login_required
def test_api(url_path: str):
    api_url = '{}/{}'.format(API_URL_BASE, url_path)

    query_data = {'token': current_user.token}
    limit = request.args.get('top', None, type=int)
    if not (limit is None or limit == ''):
        query_data['top'] = limit

    response_data = requests.get(api_url, query_data)
    return Response(response_data.text, response_data.status_code) 

##
# Error handlers
##

@app.errorhandler(404)
def handle_404(e):
    app.logger.debug('Now serving 404 page')
    return render_template('404.html'), 200

# Run:
app.debug = CONFIG.DEBUG
if app.debug:
    app.logger.setLevel(logging.DEBUG)

if __name__ == "__main__":
    app.logger.debug('Starting RESTful API test server at PORT {}'.format(CONFIG.PORT))
    app.run(port=int(CONFIG.PORT), host='0.0.0.0')

