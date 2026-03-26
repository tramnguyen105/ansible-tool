from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.credentials import Credential


class CredentialRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(self) -> list[Credential]:
        return list(self.session.scalars(select(Credential).order_by(Credential.name)).all())

    def get(self, credential_id: UUID) -> Credential | None:
        return self.session.get(Credential, credential_id)

    def get_by_name(self, name: str) -> Credential | None:
        return self.session.scalar(select(Credential).where(Credential.name == name))

    def add(self, credential: Credential) -> Credential:
        self.session.add(credential)
        self.session.flush()
        return credential

    def delete(self, credential: Credential) -> None:
        self.session.delete(credential)
