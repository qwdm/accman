import os

from flask import Flask, session
from flask_restful import Resource, Api

from .handlers import (
    ListCreateAccounts,
    Login,
    Logout,
    PasswordPolicy,
    AccountManagement,
    ChangePassword,
)

# TODO move in config
PASSWORD_TTL = 86400  # one day

app = Flask(__name__)

api = Api(
    app,
    catch_all_404s=True,
    errors={
        'Exception': {
            'message': 'error',
        },
    },
)

api.prefix = '/api/accounts'
app.secret_key = os.getenv('SECRET_KEY', '').encode('utf-8') or b'a_*2$sTdf##bNl(7*7kdkvk$@dv'

api.add_resource(ListCreateAccounts, '')
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')
api.add_resource(PasswordPolicy, '/password/policy')
api.add_resource(ChangePassword, '/id/password')
api.add_resource(AccountManagement, '/id')


if __name__ == '__main__':
    app.run(debug=True)
