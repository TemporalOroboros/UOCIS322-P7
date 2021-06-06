# Globals:
import os
import logging
import requests

import config
from flask import Flask, render_template, request

CONFIG = config.configuration()
app = Flask(__name__)
app.secret_key = os.urandom(24)

API_URL_BASE = 'http://{}:{}'.format(os.environ['RESTAPI_HOSTNAME'], os.environ['RESTAPI_PORT'])

##
# Pageserver
##

@app.route("/")
@app.route("/index")
def serve_index():
    app.logger.debug('Now serving index page')
    return render_template('api.html'), 200

##
# API Interface
##

@app.route("/test_api/<string:url_path>/<string:ret_format>")
def test_api_with_format(url_path: str, ret_format: str = ''):
    api_url = '{}/{}/{}'.format(API_URL_BASE, url_path, ret_format)
    limit = request.args.get('top', None, type=int)
    query_result = requests.get(api_url, None if (limit is None or limit == '') else {'top': limit})
    return query_result.text, query_result.status_code 

@app.route("/test_api/<string:url_path>")
def test_api(url_path: str):
    api_url = '{}/{}'.format(API_URL_BASE, url_path)
    limit = request.args.get('top', None, type=int)
    query_result = requests.get(api_url, None if (limit is None or limit == '') else {'top': limit})
    return query_result.text, query_result.status_code 

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

