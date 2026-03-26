from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.core.security import decrypt_value, encrypt_value, mask_secret
from app.models.credentials import Credential, CredentialType
from app.modules.audit.service import AuditService
from app.modules.credentials.repository import CredentialRepository
from app.modules.credentials.schemas import CredentialCreate, CredentialRead, CredentialTypeSchema, CredentialUpdate


class CredentialService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = CredentialRepository(session)
        self.audit = AuditService(session)

    def list(self) -> list[CredentialRead]:
        return [self._serialize(item) for item in self.repository.list()]

    def get(self, credential_id: UUID) -> CredentialRead:
        credential = self.repository.get(credential_id)
        if credential is None:
            raise AppError(404, 'CREDENTIAL_NOT_FOUND', 'Credential not found')
        return self._serialize(credential)

    def create(self, payload: CredentialCreate, *, user_id: UUID | None = None) -> CredentialRead:
        if self.repository.get_by_name(payload.name):
            raise AppError(409, 'CREDENTIAL_EXISTS', 'Credential name already exists')
        self._validate_payload(payload.credential_type.value, payload.password, payload.private_key)
        credential = Credential(
            name=payload.name,
            description=payload.description,
            credential_type=CredentialType(payload.credential_type.value),
            username=payload.username,
            encrypted_password=encrypt_value(payload.password),
            encrypted_private_key=encrypt_value(payload.private_key),
            encrypted_passphrase=encrypt_value(payload.passphrase),
            created_by_id=user_id,
            updated_by_id=user_id,
        )
        self.repository.add(credential)
        self.audit.record(
            action='credential.create',
            resource_type='credential',
            resource_id=str(credential.id),
            message=f'Credential {credential.name} created',
            user_id=user_id,
        )
        self.session.commit()
        return self._serialize(credential)

    def update(self, credential_id: UUID, payload: CredentialUpdate, *, user_id: UUID | None = None) -> CredentialRead:
        credential = self.repository.get(credential_id)
        if credential is None:
            raise AppError(404, 'CREDENTIAL_NOT_FOUND', 'Credential not found')

        if payload.name and payload.name != credential.name:
            existing = self.repository.get_by_name(payload.name)
            if existing and existing.id != credential.id:
                raise AppError(409, 'CREDENTIAL_EXISTS', 'Credential name already exists')
            credential.name = payload.name
        if payload.description is not None:
            credential.description = payload.description
        if payload.username is not None:
            credential.username = payload.username
        if payload.is_active is not None:
            credential.is_active = payload.is_active
        if payload.password is not None:
            credential.encrypted_password = encrypt_value(payload.password)
        if payload.private_key is not None:
            credential.encrypted_private_key = encrypt_value(payload.private_key)
        if payload.passphrase is not None:
            credential.encrypted_passphrase = encrypt_value(payload.passphrase)
        self._validate_payload(credential.credential_type.value, decrypt_value(credential.encrypted_password), decrypt_value(credential.encrypted_private_key))
        credential.updated_by_id = user_id
        self.audit.record(
            action='credential.update',
            resource_type='credential',
            resource_id=str(credential.id),
            message=f'Credential {credential.name} updated',
            user_id=user_id,
        )
        self.session.commit()
        return self._serialize(credential)

    def delete(self, credential_id: UUID, *, user_id: UUID | None = None) -> None:
        credential = self.repository.get(credential_id)
        if credential is None:
            raise AppError(404, 'CREDENTIAL_NOT_FOUND', 'Credential not found')
        self.repository.delete(credential)
        self.audit.record(
            action='credential.delete',
            resource_type='credential',
            resource_id=str(credential.id),
            message=f'Credential {credential.name} deleted',
            user_id=user_id,
        )
        self.session.commit()

    def resolve_for_execution(self, credential_id: UUID, *, user_id: UUID | None = None, job_id: str | None = None) -> dict[str, Any]:
        credential = self.repository.get(credential_id)
        if credential is None or not credential.is_active:
            raise AppError(404, 'CREDENTIAL_NOT_FOUND', 'Credential not found')
        self.audit.record(
            action='credential.use',
            resource_type='credential',
            resource_id=str(credential.id),
            message=f'Credential {credential.name} used for job execution',
            user_id=user_id,
            details={'job_id': job_id},
        )
        self.session.commit()
        return {
            'id': str(credential.id),
            'type': credential.credential_type.value,
            'username': credential.username,
            'password': decrypt_value(credential.encrypted_password),
            'private_key': decrypt_value(credential.encrypted_private_key),
            'passphrase': decrypt_value(credential.encrypted_passphrase),
        }

    def _serialize(self, credential: Credential) -> CredentialRead:
        return CredentialRead(
            id=credential.id,
            name=credential.name,
            description=credential.description,
            credential_type=credential.credential_type.value,
            username=credential.username,
            is_active=credential.is_active,
            has_password=bool(credential.encrypted_password),
            has_private_key=bool(credential.encrypted_private_key),
            has_passphrase=bool(credential.encrypted_passphrase),
        )

    def _validate_payload(self, credential_type: str, password: str | None, private_key: str | None) -> None:
        if credential_type == CredentialTypeSchema.SSH_PASSWORD.value and not password:
            raise AppError(400, 'CREDENTIAL_INVALID', 'Password credential requires a password')
        if credential_type == CredentialTypeSchema.SSH_PRIVATE_KEY.value and not private_key:
            raise AppError(400, 'CREDENTIAL_INVALID', 'SSH private key credential requires a private key')
