from __future__ import annotations

from datetime import datetime
from uuid import UUID

import yaml
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models.content import Playbook, PlaybookRevision
from app.modules.audit.service import AuditService
from app.modules.playbooks.repository import PlaybookRepository
from app.modules.playbooks.schemas import (
    PlaybookCreate,
    PlaybookRead,
    PlaybookRevisionRead,
    PlaybookSummaryRead,
    PlaybookUpdate,
    PlaybookUsageRead,
    YamlValidationResult,
)


class PlaybookService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = PlaybookRepository(session)
        self.audit = AuditService(session)

    def list(self, *, is_generated: bool | None = None) -> list[PlaybookRead]:
        return [self._serialize(item) for item in self.repository.list(is_generated=is_generated)]

    def list_summary(self, *, is_generated: bool | None = None) -> list[PlaybookSummaryRead]:
        return [self._serialize_summary(item) for item in self.repository.list(is_generated=is_generated)]

    def get(self, playbook_id: UUID) -> PlaybookRead:
        playbook = self.repository.get(playbook_id)
        if playbook is None:
            raise AppError(404, 'PLAYBOOK_NOT_FOUND', 'Playbook not found')
        return self._serialize(playbook)

    def create(self, payload: PlaybookCreate, *, user_id: UUID | None = None) -> PlaybookRead:
        name = self._normalize_required(payload.name, 'name')
        description = self._normalize_optional(payload.description)
        yaml_content = self._normalize_required(payload.yaml_content, 'yaml content')
        validation = self.validate_yaml(yaml_content)
        if not validation.valid:
            raise AppError(400, 'PLAYBOOK_YAML_INVALID', 'Invalid YAML content', {'errors': validation.errors})
        if self.repository.get_by_name_ci(name):
            raise AppError(409, 'PLAYBOOK_EXISTS', 'Playbook name already exists')
        playbook = Playbook(
            name=name,
            description=description,
            yaml_content=yaml_content,
            is_generated=payload.is_generated,
            created_by_id=user_id,
            updated_by_id=user_id,
        )
        self.repository.add(playbook)
        change_note = self._normalize_optional(payload.change_note)
        self.session.add(
            PlaybookRevision(
                playbook_id=playbook.id,
                version=1,
                yaml_content=yaml_content,
                change_note=change_note or 'Initial version',
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
        self._assert_not_stale(playbook.updated_at, payload.expected_updated_at)
        if payload.name and payload.name != playbook.name:
            normalized_name = self._normalize_required(payload.name, 'name')
            existing = self.repository.get_by_name_ci(normalized_name)
            if existing and existing.id != playbook.id:
                raise AppError(409, 'PLAYBOOK_EXISTS', 'Playbook name already exists')
            playbook.name = normalized_name
        if payload.description is not None:
            playbook.description = self._normalize_optional(payload.description)
        if payload.yaml_content is not None:
            normalized_yaml = self._normalize_required(payload.yaml_content, 'yaml content')
            validation = self.validate_yaml(normalized_yaml)
            if not validation.valid:
                raise AppError(400, 'PLAYBOOK_YAML_INVALID', 'Invalid YAML content', {'errors': validation.errors})
            playbook.yaml_content = normalized_yaml
            next_version = (playbook.revisions[0].version if playbook.revisions else 0) + 1
            change_note = self._normalize_optional(payload.change_note)
            self.session.add(
                PlaybookRevision(
                    playbook_id=playbook.id,
                    version=next_version,
                    yaml_content=normalized_yaml,
                    change_note=change_note or f'Update v{next_version}',
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
        usage = self.repository.usage(playbook_id)
        if usage['total'] > 0:
            raise AppError(
                409,
                'PLAYBOOK_IN_USE',
                'Playbook is referenced by jobs or schedules and cannot be deleted',
                usage,
            )
        self.repository.delete(playbook)
        self.audit.record(
            action='playbook.delete',
            resource_type='playbook',
            resource_id=str(playbook.id),
            message=f'Playbook {playbook.name} deleted',
            user_id=user_id,
        )
        self.session.commit()

    def usage(self, playbook_id: UUID) -> PlaybookUsageRead:
        playbook = self.repository.get(playbook_id)
        if playbook is None:
            raise AppError(404, 'PLAYBOOK_NOT_FOUND', 'Playbook not found')
        return PlaybookUsageRead(**self.repository.usage(playbook_id))

    def validate_yaml(self, content: str) -> YamlValidationResult:
        errors: list[str] = []
        parsed = None
        try:
            parsed = yaml.safe_load(content)
        except yaml.YAMLError as exc:
            mark = getattr(exc, 'problem_mark', None)
            if mark is not None:
                errors.append(f'Line {mark.line + 1}, column {mark.column + 1}: {exc}')
            else:
                errors.append(str(exc))
            return YamlValidationResult(valid=False, errors=errors)

        errors.extend(self._validate_playbook_shape(parsed))
        return YamlValidationResult(valid=not errors, errors=errors)

    def _validate_playbook_shape(self, parsed: object) -> list[str]:
        errors: list[str] = []
        if parsed is None:
            return ['Playbook cannot be empty']
        if not isinstance(parsed, list):
            return ['Top-level playbook document must be a YAML list of plays']
        if not parsed:
            return ['Playbook must contain at least one play']
        for idx, play in enumerate(parsed):
            play_pos = idx + 1
            if not isinstance(play, dict):
                errors.append(f'Play {play_pos} must be a mapping')
                continue
            hosts = play.get('hosts')
            if hosts in (None, ''):
                errors.append(f'Play {play_pos} is missing required field "hosts"')
            tasks = play.get('tasks')
            if tasks is not None and not isinstance(tasks, list):
                errors.append(f'Play {play_pos} field "tasks" must be a list when provided')
        return errors

    def _serialize(self, playbook: Playbook) -> PlaybookRead:
        revisions = [PlaybookRevisionRead.model_validate(revision) for revision in playbook.revisions]
        return PlaybookRead(
            id=playbook.id,
            name=playbook.name,
            description=playbook.description,
            yaml_content=playbook.yaml_content,
            is_generated=playbook.is_generated,
            updated_at=playbook.updated_at,
            revisions=revisions,
        )

    def _serialize_summary(self, playbook: Playbook) -> PlaybookSummaryRead:
        latest_revision = playbook.revisions[0] if playbook.revisions else None
        return PlaybookSummaryRead(
            id=playbook.id,
            name=playbook.name,
            description=playbook.description,
            is_generated=playbook.is_generated,
            revision_count=len(playbook.revisions),
            last_change_note=latest_revision.change_note if latest_revision else None,
            updated_at=playbook.updated_at,
        )

    def _normalize_required(self, value: str, field_name: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise AppError(400, 'PLAYBOOK_INVALID', f'{field_name.capitalize()} is required')
        return normalized

    def _normalize_optional(self, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    def _assert_not_stale(self, current_updated_at: datetime, expected_updated_at: datetime | None) -> None:
        if expected_updated_at is None:
            return
        if current_updated_at != expected_updated_at:
            raise AppError(
                409,
                'PLAYBOOK_EDIT_CONFLICT',
                'Playbook has been updated by another operator. Refresh and retry your changes.',
                {
                    'expected_updated_at': expected_updated_at.isoformat(),
                    'current_updated_at': current_updated_at.isoformat(),
                },
            )
