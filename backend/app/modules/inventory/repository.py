from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.models.inventory import Inventory, InventoryGroup, InventoryGroupChild, InventoryGroupHost, InventoryHost


class InventoryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(self) -> list[Inventory]:
        query = select(Inventory).options(
            selectinload(Inventory.hosts).selectinload(InventoryHost.group_links).selectinload(InventoryGroupHost.group),
            selectinload(Inventory.groups).selectinload(InventoryGroup.host_links).selectinload(InventoryGroupHost.host),
            selectinload(Inventory.groups).selectinload(InventoryGroup.child_links).selectinload(InventoryGroupChild.child_group),
        )
        return list(self.session.scalars(query).all())

    def get(self, inventory_id: UUID) -> Inventory | None:
        query = (
            select(Inventory)
            .where(Inventory.id == inventory_id)
            .options(
                selectinload(Inventory.hosts).selectinload(InventoryHost.group_links).selectinload(InventoryGroupHost.group),
                selectinload(Inventory.groups).selectinload(InventoryGroup.host_links).selectinload(InventoryGroupHost.host),
                selectinload(Inventory.groups).selectinload(InventoryGroup.child_links).selectinload(InventoryGroupChild.child_group),
            )
        )
        return self.session.scalar(query)

    def get_by_name(self, name: str) -> Inventory | None:
        return self.session.scalar(select(Inventory).where(Inventory.name == name))

    def add(self, inventory: Inventory) -> Inventory:
        self.session.add(inventory)
        self.session.flush()
        return inventory

    def delete(self, inventory: Inventory) -> None:
        self.session.delete(inventory)

    def clear_related(self, inventory: Inventory) -> None:
        self.session.execute(delete(InventoryGroupChild).where(InventoryGroupChild.parent_group_id.in_(select(InventoryGroup.id).where(InventoryGroup.inventory_id == inventory.id))))
        self.session.execute(delete(InventoryGroupHost).where(InventoryGroupHost.group_id.in_(select(InventoryGroup.id).where(InventoryGroup.inventory_id == inventory.id))))
        self.session.execute(delete(InventoryHost).where(InventoryHost.inventory_id == inventory.id))
        self.session.execute(delete(InventoryGroup).where(InventoryGroup.inventory_id == inventory.id))
