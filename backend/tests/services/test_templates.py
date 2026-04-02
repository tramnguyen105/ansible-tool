from __future__ import annotations

from uuid import uuid4

import pytest

from app.core.database import SessionLocal
from app.core.exceptions import AppError
from app.modules.templates.schemas import TemplateCreate, TemplateSourceTypeSchema, TemplateUpdate
from app.modules.templates.service import TemplateService


def test_template_create_normalizes_and_hashes_content():
    with SessionLocal() as session:
        service = TemplateService(session)
        suffix = uuid4().hex[:8]
        created = service.create(
            TemplateCreate(
                name=f'  ios-base-{suffix}  ',
                description='  baseline  ',
                content='  interface {{ name }}  ',
            )
        )
        assert created.name == f'ios-base-{suffix}'
        assert created.description == 'baseline'
        assert created.source_type == TemplateSourceTypeSchema.MANUAL
        assert len(created.content_hash) == 64
        assert created.revision == 1


def test_template_rejects_invalid_jinja():
    with SessionLocal() as session:
        service = TemplateService(session)
        suffix = uuid4().hex[:8]
        with pytest.raises(AppError) as exc:
            service.create(
                TemplateCreate(
                    name=f'broken-{suffix}',
                    description='invalid',
                    content='{% for item in items %}{{ item }}',
                )
            )
        assert exc.value.code == 'TEMPLATE_INVALID_SYNTAX'


def test_template_update_increments_revision_when_content_changes():
    with SessionLocal() as session:
        service = TemplateService(session)
        suffix = uuid4().hex[:8]
        created = service.create(
            TemplateCreate(
                name=f'router-{suffix}',
                description='desc',
                content='hostname {{ inventory_hostname }}',
            )
        )
        updated = service.update(
            created.id,
            payload=TemplateUpdate(content='hostname {{ inventory_hostname }}\n! updated'),
        )
        assert updated.revision == 2
        assert updated.content_hash != created.content_hash
