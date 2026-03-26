from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.content import Playbook


class PlaybookRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(self) -> list[Playbook]:
        return list(self.session.scalars(select(Playbook).options(selectinload(Playbook.revisions)).order_by(Playbook.name)).all())

    def get(self, playbook_id: UUID) -> Playbook | None:
        return self.session.scalar(select(Playbook).options(selectinload(Playbook.revisions)).where(Playbook.id == playbook_id))

    def get_by_name(self, name: str) -> Playbook | None:
        return self.session.scalar(select(Playbook).where(Playbook.name == name))

    def add(self, playbook: Playbook) -> Playbook:
        self.session.add(playbook)
        self.session.flush()
        return playbook

    def delete(self, playbook: Playbook) -> None:
        self.session.delete(playbook)
