from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models.content import Template
from app.modules.audit.service import AuditService
from app.modules.templates.repository import TemplateRepository
from app.modules.templates.schemas import TemplateCreate, TemplateRead, TemplateUpdate


class TemplateService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = TemplateRepository(session)
        self.audit = AuditService(session)

    def list(self) -> list[TemplateRead]:
        return [TemplateRead.model_validate(item) for item in self.repository.list()]

    def get(self, template_id: UUID) -> TemplateRead:
        template = self.repository.get(template_id)
        if template is None:
            raise AppError(404, 'TEMPLATE_NOT_FOUND', 'Template not found')
        return TemplateRead.model_validate(template)

    def create(self, payload: TemplateCreate, *, user_id: UUID | None = None) -> TemplateRead:
        if self.repository.get_by_name(payload.name):
            raise AppError(409, 'TEMPLATE_EXISTS', 'Template name already exists')
        template = Template(
            name=payload.name,
            description=payload.description,
            content=payload.content,
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
        )
        self.session.commit()
        return TemplateRead.model_validate(template)

    def update(self, template_id: UUID, payload: TemplateUpdate, *, user_id: UUID | None = None) -> TemplateRead:
        template = self.repository.get(template_id)
        if template is None:
            raise AppError(404, 'TEMPLATE_NOT_FOUND', 'Template not found')
        if payload.name and payload.name != template.name:
            existing = self.repository.get_by_name(payload.name)
            if existing and existing.id != template.id:
                raise AppError(409, 'TEMPLATE_EXISTS', 'Template name already exists')
            template.name = payload.name
        if payload.description is not None:
            template.description = payload.description
        if payload.content is not None:
            template.content = payload.content
        template.updated_by_id = user_id
        self.audit.record(
            action='template.update',
            resource_type='template',
            resource_id=str(template.id),
            message=f'Template {template.name} updated',
            user_id=user_id,
        )
        self.session.commit()
        return TemplateRead.model_validate(template)

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
