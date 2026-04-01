from __future__ import annotations

from uuid import uuid4

import pytest

from app.core.database import SessionLocal
from app.core.exceptions import AppError
from app.modules.credentials.schemas import CredentialCreate, CredentialTypeSchema
from app.modules.credentials.service import CredentialService


def test_credentials_are_masked_and_resolvable():
    with SessionLocal() as session:
        service = CredentialService(session)
        suffix = uuid4().hex[:8]
        created = service.create(
            CredentialCreate(
                name=f'router-admin-{suffix}',
                description='test',
                credential_type=CredentialTypeSchema.SSH_PASSWORD,
                username='netadmin',
                password='SuperSecret123!',
            )
        )
        assert created.has_password is True
        resolved = service.resolve_for_execution(created.id)
        assert resolved['password'] == 'SuperSecret123!'


def test_password_credentials_reject_private_key_payload():
    with SessionLocal() as session:
        service = CredentialService(session)
        suffix = uuid4().hex[:8]
        with pytest.raises(AppError) as exc:
            service.create(
                CredentialCreate(
                    name=f'invalid-password-{suffix}',
                    description='test',
                    credential_type=CredentialTypeSchema.SSH_PASSWORD,
                    username='netadmin',
                    password='SuperSecret123!',
                    private_key='-----BEGIN OPENSSH PRIVATE KEY-----\nabc\n-----END OPENSSH PRIVATE KEY-----',
                )
            )
        assert exc.value.code == 'CREDENTIAL_INVALID'


def test_private_key_credentials_reject_password_payload():
    with SessionLocal() as session:
        service = CredentialService(session)
        suffix = uuid4().hex[:8]
        with pytest.raises(AppError) as exc:
            service.create(
                CredentialCreate(
                    name=f'invalid-key-{suffix}',
                    description='test',
                    credential_type=CredentialTypeSchema.SSH_PRIVATE_KEY,
                    username='netadmin',
                    private_key='-----BEGIN OPENSSH PRIVATE KEY-----\nabc\n-----END OPENSSH PRIVATE KEY-----',
                    password='SuperSecret123!',
                )
            )
        assert exc.value.code == 'CREDENTIAL_INVALID'
