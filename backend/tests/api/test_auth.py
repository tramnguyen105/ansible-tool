from __future__ import annotations


def test_local_login_and_logout(client):
    login = client.post('/api/v1/auth/login', json={'username': 'admin', 'password': 'ChangeMe123!'})
    assert login.status_code == 200
    csrf_token = login.json()['data']['csrf_token']

    me = client.get('/api/v1/auth/me')
    assert me.status_code == 200
    assert me.json()['data']['user']['username'] == 'admin'

    logout = client.post('/api/v1/auth/logout', headers={'X-CSRF-Token': csrf_token})
    assert logout.status_code == 200
