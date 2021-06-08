"""
Replacement for RUSA ACP brevet time calculator
(see https://rusa.org/octime_acp.html)

"""

import os
import arrow # Replacement for datetime, based on moment.js
import logging
import flask
import json
import requests
import config
import acp_times
from json import loads
from datetime import timedelta
from flask import Flask, redirect, url_for, request, render_template, Response
from flask_restful import Resource, Api
from flask_login import LoginManager, current_user, login_required, login_user, logout_user, UserMixin, confirm_login, fresh_login_required
from flask_wtf import FlaskForm as Form
from wtforms import StringField, BooleanField, SelectField, validators
from pymongo import MongoClient

###
# Globals
###

CONFIG = config.configuration()
app = flask.Flask(__name__)
app.secret_key = os.urandom(24)
api = Api(app)
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


###
# Pages
###

# Main page (brevet controle time calculator)
@app.route("/index")
@app.route("/")
def index():
    app.logger.debug("Main page entry")
    login_form = LoginForm()
    return flask.render_template('calc.html', login_form=login_form)

# Display page (displays all brevet controle times in the database)
@app.route("/display")
def display():
    app.logger.debug("Display page entry")
    if not current_user.is_authenticated:
        return redirect(url_for('/index')), 401

    app.logger.debug('Fetching controle times from DB:')
    query_url = API_URL_BASE + "/controles/all"
    app.logger.debug('\tSumitting query to RESTAPI at {}'.format(query_url))

    query_result = requests.get(query_url, {'token': current_user.token})
    if query_result.status_code >= 300:
        app.logger.debug('\tEncountered error fetching from database. Status code {}'.format(query_result.status_code))
        return Response(query_result.text, query_result.status_code)

    controle_data = json.loads(query_result.text)
    if isinstance(controle_data, str):
        app.logger.debug('\tFailed to decode controle data json string: {}'.format(controle_data))
        return "", 500

    return flask.render_template('display.html', controles = controle_data)


###############
#
# AJAX request handlers
#   These return JSON, rather than rendering pages.
#
###############

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


# Calculate and return controle times
@app.route("/_calc_times")
def _calc_times():
    """
    Calculates open/close times from km using rules
    described at https://rusa.org/octime_alg.html
    Extacts three URL-encoded arguments,
        The number of km to the controle
        The distance of the brevet
        The start time of the brevet
    """
    app.logger.debug("Got a JSON request")
    km = request.args.get('km', None, type=float)
    brevet = request.args.get('brevet', 200, type=float)
    iso_start_time = request.args.get('start_time', arrow.now().isoformat, type=str)
    start_time = arrow.get(iso_start_time)

    result = acp_times.get_times_strings(km, brevet, start_time)
    return flask.jsonify(result=result), 200

# Add controle times to database
@app.route("/controles", methods=["POST"])
def add_controles_to_db():
    if not current_user.is_authenticated:
        return Response('Not logged in', 401)

    app.logger.debug("Routing POST request to RESTAPI:")

    query_url = API_URL_BASE + '/controles'
    app.logger.debug('\tSubmitting POST request to API at {}'.format(query_url))
    
    controles = request.form.get('controles', None, type=str)
    query_result = requests.post(query_url, {'data': controles, 'token': current_user.token})
    return Response(query_result.text, query_result.status_code)

###
# Error Handlers
###

@app.errorhandler(404)
def page_not_found(error):
    app.logger.debug("Page not found")
    flask.session['linkback'] = flask.url_for("index")
    return flask.render_template('404.html'), 404

@app.errorhandler(501)
def not_supported(error):
    app.logger.debug("")
    flask.session['linkback'] = flask.url_for("index")
    return flask.render_template('501.html'), 501

#############

app.debug = CONFIG.DEBUG
if app.debug:
    app.logger.setLevel(logging.DEBUG)

if __name__ == "__main__":
    app.logger.debug("Opening for global access on port {}".format(CONFIG.PORT))
    app.run(port=int(CONFIG.PORT), host="0.0.0.0")

