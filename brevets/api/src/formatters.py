# Imports:
from bson.json_util import dumps
from json import loads
from flask import jsonify

# Formatters:
def cursor_to_json(cursor):
    """ Converts a pymongo cursor to json.
    """

    return dumps(cursor)

def cursor_to_csv(cursor):
    """ Converts a pymongo cursor to csv.
    """

    documents = list(cursor)
    if len(documents) == 0:
        return ""
    
    keys = documents[0].keys()
    rows = [keys]

    for document in documents:
        rows.append([document[key] for key in keys])

    return '\n'.join(','.join(row) for row in rows)

