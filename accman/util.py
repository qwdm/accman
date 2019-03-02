from functools import wraps
from hashlib import md5
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor

from flask import session, request
from flask_restful import abort

from werkzeug.exceptions import BadRequest


def authenticated(method):
    @wraps(method)
    def wrapper(*args, **kwargs):
        if 'login' not in session:
            abort(403, error='go away')
        else:
            return method(*args, **kwargs)

    return wrapper


def superuser_only(method):
    @wraps(method)
    def wrapper(*args, **kwargs):
        if session.get('login') != 'root':
            abort(403, error='go away')
        else:
            return method(*args, **kwargs)

    return wrapper


def hash_password(password):
    return md5(password.encode('utf-8')).hexdigest()


null = type(None)  # just for beauty

def _isinstance(value, _type):
    """ fix inconsistency of isinstance(True, int) == True """

    if isinstance(_type, (list, tuple)):
        return any(_isinstance(value, t) for t in _type)

    if _type is int:
        return isinstance(value, int) and value not in {True, False}
    else:
        return isinstance(value, _type)


def validate_request_json(required_keys_types):
    """ validation decorator, use this for POST controllers
    side-effect: set self.data, underscored keys

    :param required_keys_types: dict like {'password': (str, null), 'color': str}
    """
    # check validation rules on app start
    # declared field type should be python type (int, str, bool..) or tuple/list of this types
    for key, _type in required_keys_types.items():
        if isinstance(_type, type):
            continue

        if isinstance(_type, (tuple, list)) and all(isinstance(t, type) for t in _type):
            continue

        # else
        raise Exception(f'Bad validation rule: {key}, {_type}')


    def deco(method):

        @wraps(method)
        def wrapper(self, *args, **kwargs):
            try:
                data = underscore_keys(request.json)
            except BadRequest:
                abort(400, error='Cannot decode json')

            for key, _type in required_keys_types.items():
                if key not in data:
                    abort(400, error=f'<{key}> should be provided')

                # type check and friendly error message
                if not _isinstance(data[key], _type):
                    type_strings = {
                            bool: 'boolean',
                            str: 'string',
                            int: 'integer',
                            null: 'null',
                    }
                    if isinstance(_type, (tuple, list)):
                        type_str = ' or '.join(type_strings.get(t, '<some type>') for t in _type)
                    else:
                        type_str = type_strings.get(_type, 'appropriate type')

                    abort(400, error=f'<{key}> should be {type_str}')

            self.data = data
            return method(self, *args, **kwargs)

        return wrapper

    return deco


def underscore_keys(dct):

    def _to_underscore(lowerCamelCase):
        return ''.join(f'_{c.lower()}' if c.isupper() else c for c in lowerCamelCase)

    return {_to_underscore(key): value for key, value in dct.items()}


@contextmanager
def get_db():
    # TODO from conf
    user = 'postgres'
    password = ''
    host = 'localhost'
    port = 54320
    dbname = 'accman_test'

    conn = psycopg2.connect(
    f"user='{user}' \
     password='{password}' \
     dbname='{dbname}' \
     host='{host}' \
     port={port} \
    "
    )

    try:
        yield conn.cursor(cursor_factory=RealDictCursor)
    finally:
        conn.commit()
        conn.close()
