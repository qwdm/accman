import sys
import os
import json
import pytest
import subprocess as sp

# add app to path
sys.path.append(os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '..'
))

from accman import app

class MyClient:
    def __init__(self):
        self.client = app.test_client()

        self.get = self.request('get')
        self.post = self.request('post')
        self.put = self.request('put')
        self.delete = self.request('delete')

    def request(self, method):
        return lambda url, data=None: getattr(self.client, method)(
                                                    url,
                                                    content_type='application/json',
                                                    data=json.dumps(data) if data else None,
                                            )

    def login(self, login, password=None):
        return self.post('/api/accounts/login',
                   {
                       'login': login,
                       'password': password,
                   }
               )

@pytest.fixture
def clean_base():
    # TODO consts to conf
    sp.check_call(['docker', 'exec', 'accman_postgres',
                   'psql', '-U', 'postgres', '-f', '/scripts/init.sql'])





@pytest.fixture
def client():
    yield MyClient()


@pytest.fixture
def root():
    client = MyClient()
    client.login('root', 'root')
    yield client
