import time

from .util import (
    hash_password,
    get_db,
)

# TODO move to config
PASSWORD_TTL = 86400  # one day

class ModelError(Exception):
    """ base class for business logic exceptions """

class AccountExistsAlreadyError(ModelError):
    pass

class TooWeakPasswordError(ModelError):
    pass

class ExternalPasswordCheckError(ModelError):
    pass



class Account:
    tablename = 'accounts'

    # class methods

    @classmethod
    def all_login(cls):
        with get_db() as db:
            db.execute(f'SELECT login FROM {cls.tablename}')
            login_list = [row['login'] for row in db.fetchall()]

        return login_list

    @classmethod
    def get_by_login(cls, login):
        with get_db() as db:
            db.execute(f"""
                SELECT id, login, password_hash, is_external_account, expires
                FROM {cls.tablename}
                WHERE login = %s
            """, (login,))

            row = db.fetchone()

        if row:
            return cls(**row)
        else:
            return None

    @classmethod
    def create_new(cls, login, password, is_external_account=False):
        if cls.get_by_login(login):
            raise AccountExistsAlreadyError

        if password is None and not is_external_account:
            raise ExternalPasswordCheckError

        if password is not None and is_external_account:
            raise ExternalPasswordCheckError

        if not is_external_account and not cls.is_password_allowed_by_policy(password):
            raise TooWeakPasswordError

        account_row = {
            'login': login,
            'password_hash': hash_password(password) if password else None,
            'expires': int(time.time()) + PASSWORD_TTL,
            'is_external_account': is_external_account,
        }

        with get_db() as db:
            db.execute(f"""
                INSERT INTO {cls.tablename} (login, password_hash, expires, is_external_account)
                VALUES (%(login)s, %(password_hash)s, %(expires)s, %(is_external_account)s)
            """, account_row)

        return cls.get_by_login(login)

    @classmethod
    def is_password_allowed_by_policy(cls, password):
        with get_db() as db:
            db.execute("select * from policy")
            policy = db.fetchone()

        if len(password) < policy['length']:
            return False

        is_numbers = False
        is_upper = False
        is_lower = False
        is_special = False

        for l in password:
            if l.isdigit():
                is_numbers = True
            elif l.isupper():
                is_upper = True
            elif l.islower():
                is_lower = True
            else:
                is_special = True

        return all([
            is_numbers or not policy['numbers'],
            is_upper or not policy['uppercase_letters'],
            is_lower or not policy['lowercase_letters'],
            is_special or not policy['special_symbols'],
        ])

    @classmethod
    def set_policy(cls, policy):
        with get_db() as db:
            db.execute("""UPDATE policy SET
            length = %(length)s,
            numbers = %(numbers)s,
            uppercase_letters = %(uppercase_letters)s,
            lowercase_letters = %(lowercase_letters)s,
            special_symbols = %(special_symbols)s
            """, policy)

    # instance methods

    def __init__(self,
            login=None,
            id=None,
            password_hash=None,
            expires=None,
            is_external_account=False,
    ):
        self.id = id
        self.login = login
        self.password_hash = password_hash
        self.expires = expires
        self.is_external_account = is_external_account

    def is_password_matches(self, password):
        if password is None:
            return self.password_hash is None

        return hash_password(password) == self.password_hash

    def set_password(self, new_password):

        if not self.is_password_allowed_by_policy(new_password):
            raise TooWeakPasswordError

        with get_db() as db:
            db.execute(
                f"UPDATE {self.tablename} SET password_hash = %s WHERE login = %s",
                (hash_password(new_password), self.login)
            )

    def delete(self):
        with get_db() as db:
            db.execute(f"DELETE FROM {self.tablename} WHERE login = %s", self.login)
