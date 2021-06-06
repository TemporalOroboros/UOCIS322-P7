
# RESTful API

## Maintainers:

- Ethan Killen
  - ekillen@uoregon.edu
  - killen.ethan@gmail.com
  - 541-221-0338

## Overview

The RESTful API provides a simple API for retrieving formatted data from the database of ACP controle times.
The API currently supports json and csv formatting for returned data and can selectively include controle
opening and closing times. It also supports limiting the number of returned controle times.

## Structure:

- rest\_api.py: The main program file. Handles actually setting up the URL routing.
- requirements.py: The python modules the program is dependent on.
- Dockerfile: Used to compile this entire program into an image.
- credentials-skel.ini: A template file for credentials.ini.
- app.ini: Provides some fallback config values incase credentials.ini doesn't exist.
- config.py: Provides a simple library for loading configuration files.
- src.formatters.py: Provides some basic pymongo output formatting procs.
- src.resources.py: Provides some basic resource classes to use with the flask\_restful module

## URLs

The URLs exposed by the API follow the structure '/path\_base/path\_suffix/URL\_params'
where the path\_suffix, URL\_params, and the `/` preceding them are optional.

### Path Bases:

- /listAll:
  - Indicates that both the open times and close times for each controle should be fetched from the database.
- /listOpenOnly:
  - Indicates that only the open times for each controle should be fetched from the database.
- /listCloseOnly:
  - Indicates that only the close times for each controle should be fetched from the database.

### Path Suffixes:

- json:
  - This is the default behavior if the suffix is omitted.
  - Indicates that the controle times should be returned as a json string.
- csv:
  - Indicates that the controle times should be returned as a csv string.

### URL Parameters:

- top: int (Optional)
  - Indicates the maximum number of controle times to fetch.
  - 0 or undefined does not impose a limit on the number of controles fetched.

