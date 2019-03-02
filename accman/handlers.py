from flask import session, request
from flask_restful import Resource, abort

from .util import (
    authenticated,
    superuser_only,
    validate_request_json,
    null,
)

from .model import Account
from .model import (
    AccountExistsAlreadyError,
    TooWeakPasswordError,
    ExternalPasswordCheckError,
)


class ListCreateAccounts(Resource):
    @authenticated
    def get(self):
        return {
            'loginList': Account.all_login(),
        }

    @superuser_only
    @validate_request_json({
        'login': str,
        'password': (str, null),
        'is_external_account': bool,
    })
    def post(self):
        data = self.data
        try:
            account = Account.create_new(
                data['login'],
                data['password'],
                data['is_external_account'],
            )
        except AccountExistsAlreadyError:
            abort(400, error='Account exists, cannot create')
        except TooWeakPasswordError:
            abort(400, error='Too weak password')
        except ExternalPasswordCheckError:
            abort(400, error='There should be: password == null <==> external account')

        return {
            'message': f'Account for <{account.login}> created',
        }


class Login(Resource):

    @validate_request_json({
        'login': str,
        'password': (str, null),
    })
    def post(self):
        data = self.data

        login = data['login']
        password = data['password']

        account = Account.get_by_login(login)

        if account and account.is_password_matches(password):
            session['login'] = login
            return {'message': 'Welcome home!'}
        else:
            abort(403, error='go away')


class Logout(Resource):
    def post(self):
        session.pop('login')
        return {'message': 'Good bye!'}


class PasswordPolicy(Resource):

    @superuser_only
    @validate_request_json({
        'length': int,
        'numbers': bool,
        'uppercase_letters': bool,
        'lowercase_letters': bool,
        'special_symbols': bool,
    })
    def post(self):
        Account.set_policy(self.data)
        return {'message': 'New policy was set'}


class ChangePassword(Resource):
    @authenticated
    @validate_request_json({
        'old_password': str,
        'new_password': str,
    })
    def put(self):
        data = self.data

        account = Account.get_by_login(session['login'])

        if not account:
            # in case of deleted user still have cookie
            abort(400, error='We dont know you')

        if account.is_external_account:
            abort(400, error='Cannot change password of external account')

        if not account.is_password_matches(data['old_password']):
            abort(403, error='go away')

        try:
            account.set_password(data['new_password'])
        except TooWeakPasswordError:
            abort(400, error='New password is too weak')

        return {'message': 'Password changed successfully'}


class AccountManagement(Resource):
    @authenticated
    def delete(self):
        account = Account.get_by_login(session['login'])

        if not account:
            # in case of deleted user still have cookie
            abort(400, error='We dont know you')

        account.delete()

        return {'message': 'Account was deleted successfully'}
