from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.content import Template


class TemplateRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(self) -> list[Template]:
        return list(self.session.scalars(select(Template).order_by(Template.name)).all())

    def get(self, template_id: UUID) -> Template | None:
        return self.session.get(Template, template_id)

    def get_by_name(self, name: str) -> Template | None:
        return self.session.scalar(select(Template).where(Template.name == name))

    def add(self, template: Template) -> Template:
        self.session.add(template)
        self.session.flush()
        return template

    def delete(self, template: Template) -> None:
        self.session.delete(template)
