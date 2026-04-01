from __future__ import annotations

from uuid import UUID

from sqlalchemy import case, delete, func, select
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

    def list_summary(self) -> list[dict]:
        inventories = list(self.session.scalars(select(Inventory)).all())
        if not inventories:
            return []

        inventory_ids = [item.id for item in inventories]

        host_counts_query = (
            select(
                InventoryHost.inventory_id,
                func.count(InventoryHost.id).label('host_count'),
                func.sum(case((InventoryHost.enabled.is_(True), 1), else_=0)).label('enabled_host_count'),
            )
            .where(InventoryHost.inventory_id.in_(inventory_ids))
            .group_by(InventoryHost.inventory_id)
        )

        host_counts = {
            row.inventory_id: {
                'host_count': int(row.host_count or 0),
                'enabled_host_count': int(row.enabled_host_count or 0),
            }
            for row in self.session.execute(host_counts_query)
        }
        group_counts: dict[UUID, dict[str, int]] = {}
        group_rows = self.session.execute(
            select(InventoryGroup.inventory_id, InventoryGroup.variables_json).where(InventoryGroup.inventory_id.in_(inventory_ids))
        )
        for row in group_rows:
            slot = group_counts.setdefault(row.inventory_id, {'group_count': 0, 'group_variable_scope_count': 0})
            slot['group_count'] += 1
            if row.variables_json:
                slot['group_variable_scope_count'] += 1

        output: list[dict] = []
        for inventory in inventories:
            host_meta = host_counts.get(inventory.id, {'host_count': 0, 'enabled_host_count': 0})
            group_meta = group_counts.get(inventory.id, {'group_count': 0, 'group_variable_scope_count': 0})
            output.append(
                {
                    'id': inventory.id,
                    'name': inventory.name,
                    'description': inventory.description,
                    'source_type': inventory.source_type.value,
                    'has_inventory_vars': bool(inventory.variables_json),
                    'host_count': host_meta['host_count'],
                    'enabled_host_count': host_meta['enabled_host_count'],
                    'group_count': group_meta['group_count'],
                    'group_variable_scope_count': group_meta['group_variable_scope_count'],
                }
            )
        return output

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
