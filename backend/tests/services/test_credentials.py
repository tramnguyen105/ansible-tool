from __future__ import annotations

from app.core.database import SessionLocal
from app.modules.credentials.schemas import CredentialCreate, CredentialTypeSchema
from app.modules.credentials.service import CredentialService


def test_credentials_are_masked_and_resolvable():
    with SessionLocal() as session:
        service = CredentialService(session)
        created = service.create(
            CredentialCreate(
                name='router-admin',
                description='test',
                credential_type=CredentialTypeSchema.SSH_PASSWORD,
                username='netadmin',
                password='SuperSecret123!',
            )
        )
        assert created.has_password is True
        resolved = service.resolve_for_execution(created.id)
        assert resolved['password'] == 'SuperSecret123!'
