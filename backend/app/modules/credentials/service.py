from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.core.security import decrypt_value, encrypt_value
from app.models.credentials import Credential, CredentialType
from app.models.jobs import Job, JobSchedule, JobStatus
from app.modules.audit.service import AuditService
from app.modules.credentials.repository import CredentialRepository
from app.modules.credentials.schemas import CredentialCreate, CredentialRead, CredentialTypeSchema, CredentialUpdate, CredentialUsageRead


class CredentialService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = CredentialRepository(session)
        self.audit = AuditService(session)

    def list(self, *, active_only: bool = False) -> list[CredentialRead]:
        return [self._serialize(item) for item in self.repository.list(active_only=active_only)]

    def get(self, credential_id: UUID) -> CredentialRead:
        credential = self.repository.get(credential_id)
        if credential is None:
            raise AppError(404, 'CREDENTIAL_NOT_FOUND', 'Credential not found')
        return self._serialize(credential)

    def usage(self, credential_id: UUID) -> CredentialUsageRead:
        credential = self.repository.get(credential_id)
        if credential is None:
            raise AppError(404, 'CREDENTIAL_NOT_FOUND', 'Credential not found')

        schedules_total = self.session.scalar(select(func.count(JobSchedule.id)).where(JobSchedule.credential_id == credential_id)) or 0
        schedules_enabled = self.session.scalar(
            select(func.count(JobSchedule.id)).where(JobSchedule.credential_id == credential_id, JobSchedule.enabled.is_(True))
        ) or 0
        jobs_total = self.session.scalar(select(func.count(Job.id)).where(Job.credential_id == credential_id)) or 0
        jobs_active = self.session.scalar(
            select(func.count(Job.id)).where(Job.credential_id == credential_id, Job.status.in_([JobStatus.PENDING, JobStatus.QUEUED, JobStatus.RUNNING]))
        ) or 0
        return CredentialUsageRead(
            schedules_total=int(schedules_total),
            schedules_enabled=int(schedules_enabled),
            jobs_total=int(jobs_total),
            jobs_active=int(jobs_active),
        )

    def create(self, payload: CredentialCreate, *, user_id: UUID | None = None) -> CredentialRead:
        name = self._normalize_required_text(payload.name, field='name')
        username = self._normalize_required_text(payload.username, field='username')
        description = self._normalize_optional_text(payload.description)
        password = self._normalize_secret(payload.password)
        private_key = self._normalize_secret(payload.private_key)
        passphrase = self._normalize_secret(payload.passphrase)

        if self.repository.get_by_name(name):
            raise AppError(409, 'CREDENTIAL_EXISTS', 'Credential name already exists')
        self._validate_payload(payload.credential_type.value, password, private_key, passphrase)
        credential = Credential(
            name=name,
            description=description,
            credential_type=CredentialType(payload.credential_type.value),
            username=username,
            encrypted_password=encrypt_value(password),
            encrypted_private_key=encrypt_value(private_key),
            encrypted_passphrase=encrypt_value(passphrase),
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

        if payload.name is not None:
            normalized_name = self._normalize_required_text(payload.name, field='name')
            existing = self.repository.get_by_name(normalized_name)
            if existing and existing.id != credential.id:
                raise AppError(409, 'CREDENTIAL_EXISTS', 'Credential name already exists')
            credential.name = normalized_name
        if payload.description is not None:
            credential.description = self._normalize_optional_text(payload.description)
        if payload.username is not None:
            credential.username = self._normalize_required_text(payload.username, field='username')
        if payload.is_active is not None:
            credential.is_active = payload.is_active
        if payload.password is not None:
            credential.encrypted_password = encrypt_value(self._normalize_secret(payload.password))
        if payload.private_key is not None:
            credential.encrypted_private_key = encrypt_value(self._normalize_secret(payload.private_key))
        if payload.passphrase is not None:
            credential.encrypted_passphrase = encrypt_value(self._normalize_secret(payload.passphrase))
        self._validate_payload(
            credential.credential_type.value,
            decrypt_value(credential.encrypted_password),
            decrypt_value(credential.encrypted_private_key),
            decrypt_value(credential.encrypted_passphrase),
        )
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
        usage = self.usage(credential_id)
        if usage.schedules_enabled > 0:
            raise AppError(
                409,
                'CREDENTIAL_IN_USE',
                'Credential is still referenced by enabled schedules',
                details=usage.model_dump(),
            )
        if usage.jobs_active > 0:
            raise AppError(
                409,
                'CREDENTIAL_IN_USE',
                'Credential is referenced by active jobs',
                details=usage.model_dump(),
            )
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

    def _validate_payload(self, credential_type: str, password: str | None, private_key: str | None, passphrase: str | None) -> None:
        if credential_type == CredentialTypeSchema.SSH_PASSWORD.value and not password:
            raise AppError(400, 'CREDENTIAL_INVALID', 'Password credential requires a password')
        if credential_type == CredentialTypeSchema.SSH_PASSWORD.value and private_key:
            raise AppError(400, 'CREDENTIAL_INVALID', 'Password credential cannot include an SSH private key')
        if credential_type == CredentialTypeSchema.SSH_PRIVATE_KEY.value and not private_key:
            raise AppError(400, 'CREDENTIAL_INVALID', 'SSH private key credential requires a private key')
        if credential_type == CredentialTypeSchema.SSH_PRIVATE_KEY.value and password:
            raise AppError(400, 'CREDENTIAL_INVALID', 'SSH private key credential cannot include a password')
        if passphrase and not private_key:
            raise AppError(400, 'CREDENTIAL_INVALID', 'Passphrase requires an SSH private key')

    def _normalize_required_text(self, value: str, *, field: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise AppError(400, 'CREDENTIAL_INVALID', f'{field.replace("_", " ").capitalize()} is required')
        return normalized

    def _normalize_optional_text(self, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    def _normalize_secret(self, value: str | None) -> str | None:
        if value is None:
            return None
        return value if value.strip() else None
