# API Test Website

## Maintainers:

- Ethan Killen
  - ekillen@uoregon.edu
  - killen.ethan@gmail.com
  - 541-221-0338

## Structure:

- api\_test.py: The main program file. Handles actually setting up the pageserver.
- requirements.py: The python modules the program is dependent on.
- Dockerfile: Used to compile this entire program into an image.
- credentials-skel.ini: A template file for credentials.ini.
- app.ini: Provides some fallback config values incase credentials.ini doesn't exist.
- config.py: Provides a simple library for loading configuration files.
- static/: Holds the .css and .js resources used by the pageserver.
- templates/: Holds the .html template files used by the pageserver.

## Overview

The API Test Website provides a simple interface for the RESTful API module.
It provides the ability to make customized requests to the API.
The data retrieved by the most recent request is displayed in the page to the right.

Options:
 - You can specify whether to retrieve open times, close times, or both.
 - You can specify whether to retrieve the data in json or csv format.
 - You can specify the maximum number of controle times to retrieve.

