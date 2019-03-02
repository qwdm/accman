import json
import pytest

from conftest import MyClient

def test_login(client, clean_base):
    """
    test login as root and make simple authenticated action
    """
    # should not be allowed
    assert client.get('/api/accounts').status_code == 403

    assert client.login('root', 'root').status_code == 200

    resp = client.get('/api/accounts')
    assert resp.status_code == 200
    assert resp.json['loginList'] == ['root']


def test_add_account(root, clean_base):
    """
    Cases:
        1. by root: new internal/external account -> OK
        2. by root: try to add login with existing account -> 400
        3. by root: try to add internal without password/external with password -> 400
        4. by ordinary user: try to add account -> 403
    """
    # 1. by root: OK
    assert root.post('/api/accounts', {
        'login': 'vasya',
        'password': '123456',
        'isExternalAccount': False,
    }).status_code == 200

    assert root.post('/api/accounts', {
        'login': 'gennadiy',
        'password': None,
        'isExternalAccount': True,
    }).status_code == 200

    resp = root.get('/api/accounts')
    assert resp.status_code == 200
    assert set(resp.json['loginList']) == set(['root', 'vasya', 'gennadiy'])

    # 2. by root: existing -> 400
    assert root.post('/api/accounts', {
        'login': 'vasya',
        'password': 'oops',
        'isExternalAccount': False,
    }).status_code == 400

    # 3. by root: bad data -> 400
    assert root.post('/api/accounts', {
        'login': 'petya',
        'password': None,
        'isExternalAccount': False,
    }).status_code == 400

    assert root.post('/api/accounts', {
        'login': 'petya',
        'password': 'yourmama',
        'isExternalAccount': True,
    }).status_code == 400

    # 4. by ordinary client: forbidden, 403
    client = MyClient()
    assert client.login('vasya', '123456').status_code == 200
    assert client.post('/api/accounts', {
        'login': 'petya',
        'password': 'woops',
        'isExternalAccount': False,
    }).status_code == 403


def test_password_policy(root, clean_base):
    """
    Cases:
        1. Send some sorts of bad policy data -> 400
        2. Send good policy and check to create new account and change password
    """
    # 1. Bad policies
    bad_policies = [
        {
            'titsSize': 5,
            'iq': 160,
        },
        {
            'length': 5,
            'numbers': True,
        },
        {
            'length': True,
            'numbers': True,
            'uppercaseLetters': True,
            'lowercaseLetters': True,
            'specialSymbols': True,
        }
    ]

    for policy in bad_policies:
        assert root.post('/api/accounts/password/policy', policy).status_code == 400

    # and one still can make account with weak password (default policy isn't strong at all)
    assert root.post('/api/accounts', {
        'login': 'gavrila',
        'password': 'a',
        'isExternalAccount': False,
    }).status_code == 200

    # 2. Good policy

    assert root.post('/api/accounts/password/policy', {
        'length': 8,
        'numbers': True,
        'uppercaseLetters': True,
        'lowercaseLetters': True,
        'specialSymbols': True,
    }).status_code == 200

    # cannot create account with weak password
    assert root.post('/api/accounts', {
        'login': 'nikitka',
        'password': 'lol',
        'isExternalAccount': False,
    }).status_code == 400

    # but one can create account with strong enough password
    assert root.post('/api/accounts', {
        'login': 'john lennon',
        'password': 'pa$$w0_rD',
        'isExternalAccount': False,
    }).status_code == 200

    resp = root.get('/api/accounts')

    assert 'john lennon' in resp.json['loginList']

    # weak -> 400
    assert root.put('/api/accounts/id/password', {
        'oldPassword': 'root',
        'newPassword': 'bazz',
    }).status_code == 400

    # strong enough -> 200
    assert root.put('/api/accounts/id/password', {
        'oldPassword': 'root',
        'newPassword': 'VeR*5trong',
    }).status_code == 200
