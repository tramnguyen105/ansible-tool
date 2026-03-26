from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import JSON, Boolean, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.jobs import Job, JobSchedule


class InventorySourceType(StrEnum):
    MANUAL = 'manual'
    IMPORT = 'import'


class Inventory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = 'inventories'

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    source_type: Mapped[InventorySourceType] = mapped_column(Enum(InventorySourceType), default=InventorySourceType.MANUAL)
    variables_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    raw_import: Mapped[str | None] = mapped_column(Text)

    hosts: Mapped[list['InventoryHost']] = relationship('InventoryHost', back_populates='inventory', cascade='all, delete-orphan')
    groups: Mapped[list['InventoryGroup']] = relationship('InventoryGroup', back_populates='inventory', cascade='all, delete-orphan')
    jobs: Mapped[list['Job']] = relationship('Job', back_populates='inventory')
    schedules: Mapped[list['JobSchedule']] = relationship('JobSchedule', back_populates='inventory')


class InventoryHost(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = 'inventory_hosts'
    __table_args__ = (UniqueConstraint('inventory_id', 'name', name='uq_inventory_hosts_inventory_id_name'),)

    inventory_id: Mapped[UUID] = mapped_column(ForeignKey('inventories.id', ondelete='CASCADE'), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    variables_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    inventory: Mapped[Inventory] = relationship('Inventory', back_populates='hosts')
    group_links: Mapped[list['InventoryGroupHost']] = relationship('InventoryGroupHost', back_populates='host', cascade='all, delete-orphan')


class InventoryGroup(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = 'inventory_groups'
    __table_args__ = (UniqueConstraint('inventory_id', 'name', name='uq_inventory_groups_inventory_id_name'),)

    inventory_id: Mapped[UUID] = mapped_column(ForeignKey('inventories.id', ondelete='CASCADE'), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    variables_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    inventory: Mapped[Inventory] = relationship('Inventory', back_populates='groups')
    host_links: Mapped[list['InventoryGroupHost']] = relationship('InventoryGroupHost', back_populates='group', cascade='all, delete-orphan')
    child_links: Mapped[list['InventoryGroupChild']] = relationship(
        'InventoryGroupChild',
        foreign_keys='InventoryGroupChild.parent_group_id',
        back_populates='parent_group',
        cascade='all, delete-orphan',
    )
    parent_links: Mapped[list['InventoryGroupChild']] = relationship(
        'InventoryGroupChild',
        foreign_keys='InventoryGroupChild.child_group_id',
        back_populates='child_group',
        cascade='all, delete-orphan',
    )


class InventoryGroupHost(Base):
    __tablename__ = 'inventory_group_hosts'
    __table_args__ = (UniqueConstraint('group_id', 'host_id', name='uq_inventory_group_hosts_group_id_host_id'),)

    group_id: Mapped[UUID] = mapped_column(ForeignKey('inventory_groups.id', ondelete='CASCADE'), primary_key=True)
    host_id: Mapped[UUID] = mapped_column(ForeignKey('inventory_hosts.id', ondelete='CASCADE'), primary_key=True)

    group: Mapped[InventoryGroup] = relationship('InventoryGroup', back_populates='host_links')
    host: Mapped[InventoryHost] = relationship('InventoryHost', back_populates='group_links')


class InventoryGroupChild(Base):
    __tablename__ = 'inventory_group_children'
    __table_args__ = (UniqueConstraint('parent_group_id', 'child_group_id', name='uq_inventory_group_children_parent_child'),)

    parent_group_id: Mapped[UUID] = mapped_column(ForeignKey('inventory_groups.id', ondelete='CASCADE'), primary_key=True)
    child_group_id: Mapped[UUID] = mapped_column(ForeignKey('inventory_groups.id', ondelete='CASCADE'), primary_key=True)

    parent_group: Mapped[InventoryGroup] = relationship('InventoryGroup', foreign_keys=[parent_group_id], back_populates='child_links')
    child_group: Mapped[InventoryGroup] = relationship('InventoryGroup', foreign_keys=[child_group_id], back_populates='parent_links')
