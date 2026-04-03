from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.core.database import SessionLocal
from app.models.content import Playbook
from app.models.credentials import Credential, CredentialType
from app.models.inventory import Inventory, InventoryGroup, InventoryHost, InventorySourceType
from app.models.jobs import Job, JobStatus


def _login(client) -> None:
    response = client.post('/api/v1/auth/login', json={'username': 'admin', 'password': 'ChangeMe123!'})
    assert response.status_code == 200


def _seed_query_data():
    with SessionLocal() as session:
        credential = Credential(
            name='Core SSH',
            credential_type=CredentialType.SSH_PASSWORD,
            username='netops',
            encrypted_password='encrypted',
            is_active=True,
        )
        playbook = Playbook(name='Deploy Core', yaml_content='- hosts: all', is_generated=False)
        session.add_all([credential, playbook])
        session.flush()

        core = Inventory(
            name='Core Devices',
            description='Primary backbone routers',
            source_type=InventorySourceType.MANUAL,
            variables_json={'site': 'core'},
        )
        branch = Inventory(
            name='Branch Import',
            description='Imported branch switches',
            source_type=InventorySourceType.IMPORT,
            variables_json={},
        )
        empty = Inventory(
            name='Empty Shell',
            description='No devices yet',
            source_type=InventorySourceType.MANUAL,
            variables_json={},
        )
        session.add_all([core, branch, empty])
        session.flush()

        core_group = InventoryGroup(inventory_id=core.id, name='wan', variables_json={'role': 'core'})
        branch_group = InventoryGroup(inventory_id=branch.id, name='access', variables_json={})
        session.add_all([core_group, branch_group])
        session.flush()

        session.add_all(
            [
                InventoryHost(inventory_id=core.id, name='core-rtr-01', address='10.0.0.1', enabled=True, variables_json={}),
                InventoryHost(inventory_id=core.id, name='core-rtr-02', address='10.0.0.2', enabled=False, variables_json={}),
                InventoryHost(inventory_id=branch.id, name='branch-sw-01', address='10.1.0.10', enabled=True, variables_json={}),
            ]
        )

        now = datetime.now(timezone.utc)
        session.add_all(
            [
                Job(
                    name='Core Deploy',
                    status=JobStatus.SUCCESS,
                    inventory_id=core.id,
                    credential_id=credential.id,
                    playbook_id=playbook.id,
                    target_type='group',
                    target_value='wan',
                    check_mode=False,
                    created_at=now - timedelta(hours=3),
                ),
                Job(
                    name='Core Check',
                    status=JobStatus.FAILED,
                    inventory_id=core.id,
                    credential_id=credential.id,
                    playbook_id=playbook.id,
                    target_type='host',
                    target_value='core-rtr-01',
                    check_mode=True,
                    created_at=now - timedelta(hours=2),
                ),
                Job(
                    name='Branch Rollout',
                    status=JobStatus.RUNNING,
                    inventory_id=branch.id,
                    credential_id=credential.id,
                    playbook_id=playbook.id,
                    target_type='all',
                    target_value=None,
                    check_mode=False,
                    created_at=now - timedelta(hours=1),
                ),
            ]
        )
        session.commit()


def test_query_jobs_supports_search_filters_and_pagination(client):
    _seed_query_data()
    _login(client)

    response = client.get(
        '/api/v1/jobs/query',
        params=[
            ('search', 'Core'),
            ('statuses', 'failed'),
            ('mode', 'check'),
            ('limit', '1'),
            ('offset', '0'),
            ('sort_by', 'name'),
            ('sort_order', 'asc'),
        ],
    )

    assert response.status_code == 200
    payload = response.json()['data']
    assert payload['total'] == 1
    assert payload['limit'] == 1
    assert payload['offset'] == 0
    assert payload['has_more'] is False
    assert [item['name'] for item in payload['items']] == ['Core Check']


def test_query_inventory_summary_supports_filters_and_pagination(client):
    _seed_query_data()
    _login(client)

    response = client.get(
        '/api/v1/inventories/summary/query',
        params=[
            ('source_types', 'manual'),
            ('readiness', 'ready'),
            ('limit', '1'),
            ('offset', '0'),
            ('sort_by', 'name'),
            ('sort_order', 'asc'),
        ],
    )

    assert response.status_code == 200
    payload = response.json()['data']
    assert payload['total'] == 1
    assert payload['has_more'] is False
    assert len(payload['items']) == 1
    assert payload['items'][0]['name'] == 'Core Devices'
    assert payload['items'][0]['readiness'] == 'ready'


def test_query_inventory_summary_search_returns_expected_page(client):
    _seed_query_data()
    _login(client)

    response = client.get(
        '/api/v1/inventories/summary/query',
        params=[
            ('search', 'Import'),
            ('limit', '10'),
            ('offset', '0'),
        ],
    )

    assert response.status_code == 200
    payload = response.json()['data']
    assert payload['total'] == 1
    assert [item['name'] for item in payload['items']] == ['Branch Import']
