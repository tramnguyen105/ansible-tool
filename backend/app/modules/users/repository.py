from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.auth import Role, User, UserRole


class UsersRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_users(self) -> list[User]:
        return list(
            self.session.scalars(
                select(User).options(joinedload(User.roles)).order_by(User.username.asc())
            ).unique().all()
        )

    def get_user(self, user_id: UUID) -> User | None:
        return self.session.scalar(select(User).options(joinedload(User.roles)).where(User.id == user_id))

    def get_user_by_username(self, username: str) -> User | None:
        return self.session.scalar(select(User).options(joinedload(User.roles)).where(User.username == username))

    def list_roles(self) -> list[Role]:
        return list(self.session.scalars(select(Role).order_by(Role.name.asc())).all())

    def get_role_by_name(self, role_name: str) -> Role | None:
        return self.session.scalar(select(Role).where(Role.name == role_name))

    def create_role(self, role_name: str) -> Role:
        role = Role(name=role_name, description=f'{role_name.title()} role')
        self.session.add(role)
        self.session.flush()
        return role

    def set_user_roles(self, user: User, role_names: list[str]) -> None:
        desired_names = sorted(set(name.strip() for name in role_names if name.strip()))
        roles: list[Role] = []
        for role_name in desired_names:
            role = self.get_role_by_name(role_name) or self.create_role(role_name)
            roles.append(role)
        self.session.query(UserRole).filter(UserRole.user_id == user.id).delete(synchronize_session=False)
        for role in roles:
            self.session.add(UserRole(user_id=user.id, role_id=role.id, created_at=datetime.now(timezone.utc)))
        self.session.flush()
        self.session.refresh(user)
