from __future__ import annotations

from uuid import UUID

import yaml
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models.content import Playbook, PlaybookRevision
from app.modules.audit.service import AuditService
from app.modules.playbooks.repository import PlaybookRepository
from app.modules.playbooks.schemas import PlaybookCreate, PlaybookRead, PlaybookRevisionRead, PlaybookUpdate, YamlValidationResult


class PlaybookService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = PlaybookRepository(session)
        self.audit = AuditService(session)

    def list(self) -> list[PlaybookRead]:
        return [self._serialize(item) for item in self.repository.list()]

    def get(self, playbook_id: UUID) -> PlaybookRead:
        playbook = self.repository.get(playbook_id)
        if playbook is None:
            raise AppError(404, 'PLAYBOOK_NOT_FOUND', 'Playbook not found')
        return self._serialize(playbook)

    def create(self, payload: PlaybookCreate, *, user_id: UUID | None = None) -> PlaybookRead:
        validation = self.validate_yaml(payload.yaml_content)
        if not validation.valid:
            raise AppError(400, 'PLAYBOOK_YAML_INVALID', 'Invalid YAML content', {'errors': validation.errors})
        if self.repository.get_by_name(payload.name):
            raise AppError(409, 'PLAYBOOK_EXISTS', 'Playbook name already exists')
        playbook = Playbook(
            name=payload.name,
            description=payload.description,
            yaml_content=payload.yaml_content,
            is_generated=payload.is_generated,
            created_by_id=user_id,
            updated_by_id=user_id,
        )
        self.repository.add(playbook)
        self.session.add(
            PlaybookRevision(
                playbook_id=playbook.id,
                version=1,
                yaml_content=payload.yaml_content,
                change_note=payload.change_note or 'Initial version',
                edited_by_id=user_id,
            )
        )
        self.audit.record(
            action='playbook.create',
            resource_type='playbook',
            resource_id=str(playbook.id),
            message=f'Playbook {playbook.name} created',
            user_id=user_id,
        )
        self.session.commit()
        return self.get(playbook.id)

    def update(self, playbook_id: UUID, payload: PlaybookUpdate, *, user_id: UUID | None = None) -> PlaybookRead:
        playbook = self.repository.get(playbook_id)
        if playbook is None:
            raise AppError(404, 'PLAYBOOK_NOT_FOUND', 'Playbook not found')
        if payload.name and payload.name != playbook.name:
            existing = self.repository.get_by_name(payload.name)
            if existing and existing.id != playbook.id:
                raise AppError(409, 'PLAYBOOK_EXISTS', 'Playbook name already exists')
            playbook.name = payload.name
        if payload.description is not None:
            playbook.description = payload.description
        if payload.yaml_content is not None:
            validation = self.validate_yaml(payload.yaml_content)
            if not validation.valid:
                raise AppError(400, 'PLAYBOOK_YAML_INVALID', 'Invalid YAML content', {'errors': validation.errors})
            playbook.yaml_content = payload.yaml_content
            next_version = (playbook.revisions[0].version if playbook.revisions else 0) + 1
            self.session.add(
                PlaybookRevision(
                    playbook_id=playbook.id,
                    version=next_version,
                    yaml_content=payload.yaml_content,
                    change_note=payload.change_note or f'Update v{next_version}',
                    edited_by_id=user_id,
                )
            )
        playbook.updated_by_id = user_id
        self.audit.record(
            action='playbook.update',
            resource_type='playbook',
            resource_id=str(playbook.id),
            message=f'Playbook {playbook.name} updated',
            user_id=user_id,
        )
        self.session.commit()
        return self.get(playbook.id)

    def delete(self, playbook_id: UUID, *, user_id: UUID | None = None) -> None:
        playbook = self.repository.get(playbook_id)
        if playbook is None:
            raise AppError(404, 'PLAYBOOK_NOT_FOUND', 'Playbook not found')
        self.repository.delete(playbook)
        self.audit.record(
            action='playbook.delete',
            resource_type='playbook',
            resource_id=str(playbook.id),
            message=f'Playbook {playbook.name} deleted',
            user_id=user_id,
        )
        self.session.commit()

    def validate_yaml(self, content: str) -> YamlValidationResult:
        errors: list[str] = []
        try:
            yaml.safe_load(content)
        except yaml.YAMLError as exc:
            errors.append(str(exc))
        return YamlValidationResult(valid=not errors, errors=errors)

    def _serialize(self, playbook: Playbook) -> PlaybookRead:
        revisions = [PlaybookRevisionRead.model_validate(revision) for revision in playbook.revisions]
        return PlaybookRead(
            id=playbook.id,
            name=playbook.name,
            description=playbook.description,
            yaml_content=playbook.yaml_content,
            is_generated=playbook.is_generated,
            revisions=revisions,
        )
