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
from flask import Flask, redirect, url_for, request, render_template
from flask_restful import Resource, Api
from pymongo import MongoClient

###
# Globals
###

CONFIG = config.configuration()
app = flask.Flask(__name__)
app.secret_key = os.urandom(24)
api = Api(app)

API_URL_BASE = 'http://{}:{}'.format(os.environ['RESTAPI_HOSTNAME'], os.environ['RESTAPI_PORT'])

###
# Pages
###

# Main page (brevet controle time calculator)
@app.route("/")
@app.route("/index")
def index():
    app.logger.debug("Main page entry")
    return flask.render_template('calc.html')

# Display page (displays all brevet controle times in the database)
@app.route("/display")
def display():
    app.logger.debug("Display page entry")

    app.logger.debug('Fetching controle times from DB:')
    query_url = API_URL_BASE + "/controles/all"
    app.logger.debug('\tSumitting query to RESTAPI at {}'.format(query_url))

    query_result = requests.get(query_url)
    if query_result.status_code > 299:
        app.logger.debug('\tEncountered error fetching from database. Status code {}'.format(query_result.status_code))
        return query_result.text, query_result.status_code

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
    return flask.jsonify(result=result)

# Add controle times to database
@app.route("/controles", methods=["POST"])
def add_controles_to_db():
    app.logger.debug("Routing POST request to RESTAPI:")

    query_url = API_URL_BASE + '/controles'
    app.logger.debug('\tSubmitting POST request to API at {}'.format(query_url))
    
    controles = request.form.get('controles', None, type=str)
    query_result = requests.post(query_url, {'data': controles})
    return query_result.text, query_result.status_code

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

