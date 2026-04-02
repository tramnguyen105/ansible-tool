from __future__ import annotations

from hashlib import sha256
from uuid import UUID

from jinja2 import Environment, TemplateSyntaxError
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models.content import Template
from app.modules.audit.service import AuditService
from app.modules.templates.repository import TemplateRepository
from app.modules.templates.schemas import (
    TemplateCreate,
    TemplateRead,
    TemplateSourceTypeSchema,
    TemplateSummaryRead,
    TemplateUpdate,
    TemplateValidateRead,
)


class TemplateService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = TemplateRepository(session)
        self.audit = AuditService(session)

    def list_summary(self, *, source_type: TemplateSourceTypeSchema | None = None) -> list[TemplateSummaryRead]:
        source = source_type.value if source_type else None
        return [self._serialize_summary(item) for item in self.repository.list(source_type=source)]

    def list(self, *, source_type: TemplateSourceTypeSchema | None = None) -> list[TemplateRead]:
        source = source_type.value if source_type else None
        return [self._serialize(item) for item in self.repository.list(source_type=source)]

    def get(self, template_id: UUID) -> TemplateRead:
        template = self.repository.get(template_id)
        if template is None:
            raise AppError(404, 'TEMPLATE_NOT_FOUND', 'Template not found')
        return self._serialize(template)

    def create(
        self,
        payload: TemplateCreate,
        *,
        user_id: UUID | None = None,
        source_type: TemplateSourceTypeSchema = TemplateSourceTypeSchema.MANUAL,
        conversion_job_id: UUID | None = None,
    ) -> TemplateRead:
        name = self._normalize_required_text(payload.name, field='name')
        description = self._normalize_optional_text(payload.description)
        content = self._normalize_required_text(payload.content, field='content')
        self.validate_content(content)

        if self.repository.get_by_name(name):
            raise AppError(409, 'TEMPLATE_EXISTS', 'Template name already exists')
        template = Template(
            name=name,
            description=description,
            content=content,
            source_type=source_type.value,
            conversion_job_id=conversion_job_id,
            content_hash=self._compute_content_hash(content),
            revision=1,
            created_by_id=user_id,
            updated_by_id=user_id,
        )
        self.repository.add(template)
        self.audit.record(
            action='template.create',
            resource_type='template',
            resource_id=str(template.id),
            message=f'Template {template.name} created',
            user_id=user_id,
            details={'source_type': template.source_type, 'conversion_job_id': str(conversion_job_id) if conversion_job_id else None},
        )
        self.session.commit()
        return self._serialize(template)

    def update(self, template_id: UUID, payload: TemplateUpdate, *, user_id: UUID | None = None) -> TemplateRead:
        template = self.repository.get(template_id)
        if template is None:
            raise AppError(404, 'TEMPLATE_NOT_FOUND', 'Template not found')
        if payload.name is not None:
            normalized_name = self._normalize_required_text(payload.name, field='name')
            existing = self.repository.get_by_name(normalized_name)
            if existing and existing.id != template.id:
                raise AppError(409, 'TEMPLATE_EXISTS', 'Template name already exists')
            template.name = normalized_name
        if payload.description is not None:
            template.description = self._normalize_optional_text(payload.description)
        content_changed = False
        if payload.content is not None:
            normalized_content = self._normalize_required_text(payload.content, field='content')
            self.validate_content(normalized_content)
            if normalized_content != template.content:
                template.content = normalized_content
                template.content_hash = self._compute_content_hash(normalized_content)
                content_changed = True
        if content_changed:
            template.revision = int(template.revision or 1) + 1
        template.updated_by_id = user_id
        self.audit.record(
            action='template.update',
            resource_type='template',
            resource_id=str(template.id),
            message=f'Template {template.name} updated',
            user_id=user_id,
            details={'content_changed': content_changed, 'revision': template.revision},
        )
        self.session.commit()
        return self._serialize(template)

    def delete(self, template_id: UUID, *, user_id: UUID | None = None) -> None:
        template = self.repository.get(template_id)
        if template is None:
            raise AppError(404, 'TEMPLATE_NOT_FOUND', 'Template not found')
        self.repository.delete(template)
        self.audit.record(
            action='template.delete',
            resource_type='template',
            resource_id=str(template.id),
            message=f'Template {template.name} deleted',
            user_id=user_id,
        )
        self.session.commit()

    def validate_content(self, content: str) -> TemplateValidateRead:
        normalized_content = self._normalize_required_text(content, field='content')
        try:
            Environment().parse(normalized_content)
            return TemplateValidateRead(valid=True, message='Template syntax is valid')
        except TemplateSyntaxError as exc:
            raise AppError(
                400,
                'TEMPLATE_INVALID_SYNTAX',
                'Template content contains invalid Jinja syntax',
                details={
                    'line': exc.lineno,
                    'name': exc.name,
                    'error': str(exc),
                },
            ) from exc

    def _serialize_summary(self, template: Template) -> TemplateSummaryRead:
        return TemplateSummaryRead(
            id=template.id,
            name=template.name,
            description=template.description,
            source_type=TemplateSourceTypeSchema(template.source_type),
            conversion_job_id=template.conversion_job_id,
            content_hash=template.content_hash,
            revision=template.revision,
            created_at=template.created_at,
            updated_at=template.updated_at,
            preview=self._preview_text(template.content),
        )

    def _serialize(self, template: Template) -> TemplateRead:
        return TemplateRead(
            **self._serialize_summary(template).model_dump(),
            content=template.content,
        )

    def _normalize_required_text(self, value: str, *, field: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise AppError(400, 'TEMPLATE_INVALID', f'{field.replace("_", " ").capitalize()} is required')
        return normalized

    def _normalize_optional_text(self, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    def _compute_content_hash(self, content: str) -> str:
        return sha256(content.encode('utf-8')).hexdigest()

    def _preview_text(self, content: str, length: int = 180) -> str:
        flattened = ' '.join(content.split())
        return flattened[:length]
