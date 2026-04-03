from __future__ import annotations

from uuid import UUID

from sqlalchemy import case, delete, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.inventory import Inventory, InventoryGroup, InventoryGroupChild, InventoryGroupHost, InventoryHost, InventorySourceType
from app.models.system import InventoryImportPreviewToken


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

    def list_summary_filtered(
        self,
        *,
        search: str | None = None,
        source_types: list[str] | None = None,
        readiness: list[str] | None = None,
        limit: int = 25,
        offset: int = 0,
        sort_by: str = 'name',
        sort_order: str = 'asc',
    ) -> tuple[list[dict], int, dict[str, int]]:
        requires_readiness_postfilter = bool(readiness)
        filters = []
        if search:
            term = f'%{search.strip()}%'
            filters.append(or_(Inventory.name.ilike(term), Inventory.description.ilike(term)))
        if source_types:
            normalized_sources = [item for item in source_types if item in {source.value for source in InventorySourceType}]
            if normalized_sources:
                filters.append(Inventory.source_type.in_(normalized_sources))

        total = self.session.scalar(select(func.count()).select_from(Inventory).where(*filters)) or 0
        sort_column = {
            'name': Inventory.name,
            'source_type': Inventory.source_type,
            'created_at': Inventory.created_at,
            'updated_at': Inventory.updated_at,
        }.get(sort_by, Inventory.name)
        order_column = sort_column.asc() if sort_order == 'asc' else sort_column.desc()
        inventories = list(
            self.session.scalars(
                select(Inventory)
                .where(*filters)
                .order_by(order_column, Inventory.name.asc())
                .limit(limit if not requires_readiness_postfilter else None)
                .offset(offset if not requires_readiness_postfilter else None)
            ).all()
        )
        if not inventories:
            return [], int(total), {
                'inventories': 0,
                'hosts': 0,
                'enabled_hosts': 0,
                'groups': 0,
                'variable_bearing': 0,
            }

        stat_inventories = inventories if requires_readiness_postfilter else list(
            self.session.scalars(select(Inventory).where(*filters)).all()
        )
        inventory_ids = [item.id for item in stat_inventories] if stat_inventories else [item.id for item in inventories]
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

        if readiness:
            allowed = set(readiness)
            output = [row for row in output if self._summary_readiness(row) in allowed]
            total = len(output)
            output = output[offset : offset + limit]
        stats_source = [
            {
                'id': inventory.id,
                'name': inventory.name,
                'description': inventory.description,
                'source_type': inventory.source_type.value,
                'has_inventory_vars': bool(inventory.variables_json),
                'host_count': host_counts.get(inventory.id, {'host_count': 0})['host_count'],
                'enabled_host_count': host_counts.get(inventory.id, {'enabled_host_count': 0})['enabled_host_count'],
                'group_count': group_counts.get(inventory.id, {'group_count': 0})['group_count'],
                'group_variable_scope_count': group_counts.get(inventory.id, {'group_variable_scope_count': 0})['group_variable_scope_count'],
            }
            for inventory in stat_inventories
        ]
        if readiness:
            allowed = set(readiness)
            stats_source = [item for item in stats_source if self._summary_readiness(item) in allowed]
        stats = {
            'inventories': len(stats_source),
            'hosts': sum(int(item['host_count']) for item in stats_source),
            'enabled_hosts': sum(int(item['enabled_host_count']) for item in stats_source),
            'groups': sum(int(item['group_count']) for item in stats_source),
            'variable_bearing': sum(1 for item in stats_source if int(item['group_variable_scope_count']) > 0 or bool(item['has_inventory_vars'])),
        }
        return output, int(total), stats

    def _summary_readiness(self, inventory: dict) -> str:
        host_count = int(inventory['host_count'])
        enabled_host_count = int(inventory['enabled_host_count'])
        if not host_count:
            return 'incomplete'
        if host_count and not enabled_host_count:
            return 'disabled'
        if host_count and enabled_host_count:
            return 'ready'
        return 'review'

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

    def add_preview_token(
        self,
        *,
        preview_id: str,
        checksum: str,
        expires_at,
        payload_json: dict,
    ) -> InventoryImportPreviewToken:
        token = InventoryImportPreviewToken(
            preview_id=preview_id,
            checksum=checksum,
            expires_at=expires_at,
            payload_json=payload_json,
        )
        self.session.add(token)
        self.session.flush()
        return token

    def get_preview_token(self, preview_id: str) -> InventoryImportPreviewToken | None:
        return self.session.scalar(
            select(InventoryImportPreviewToken).where(InventoryImportPreviewToken.preview_id == preview_id)
        )

    def delete_preview_token(self, token: InventoryImportPreviewToken) -> None:
        self.session.delete(token)
        self.session.flush()

    def purge_expired_preview_tokens(self, *, now) -> None:
        self.session.execute(
            delete(InventoryImportPreviewToken).where(InventoryImportPreviewToken.expires_at < now)
        )
        self.session.flush()
