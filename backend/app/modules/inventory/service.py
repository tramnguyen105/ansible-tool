from __future__ import annotations

import io
import shlex
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

import pandas as pd
import yaml
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models.inventory import Inventory, InventoryGroup, InventoryGroupChild, InventoryGroupHost, InventoryHost, InventorySourceType
from app.modules.audit.service import AuditService
from app.modules.inventory.repository import InventoryRepository
from app.modules.inventory.schemas import (
    ImportFormat,
    InventoryCreate,
    InventoryGroupInput,
    InventoryGroupRead,
    InventoryHostInput,
    InventoryHostRead,
    InventoryImportCommit,
    InventoryImportPreview,
    InventoryRead,
    InventoryUpdate,
)


@dataclass
class NormalizedHost:
    name: str
    address: str | None = None
    description: str | None = None
    variables: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    groups: set[str] = field(default_factory=set)


@dataclass
class NormalizedGroup:
    name: str
    description: str | None = None
    variables: dict[str, Any] = field(default_factory=dict)
    children: set[str] = field(default_factory=set)


class InventoryService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = InventoryRepository(session)
        self.audit = AuditService(session)

    def list(self) -> list[InventoryRead]:
        return [self._serialize(item) for item in self.repository.list()]

    def get(self, inventory_id: UUID) -> InventoryRead:
        inventory = self.repository.get(inventory_id)
        if inventory is None:
            raise AppError(404, 'INVENTORY_NOT_FOUND', 'Inventory not found')
        return self._serialize(inventory)

    def create(self, payload: InventoryCreate, *, user_id: UUID | None = None) -> InventoryRead:
        if self.repository.get_by_name(payload.name):
            raise AppError(409, 'INVENTORY_EXISTS', 'Inventory name already exists')

        inventory = Inventory(
            name=payload.name,
            description=payload.description,
            source_type=InventorySourceType.MANUAL,
            variables_json=payload.variables,
        )
        self.repository.add(inventory)
        self._persist_members(inventory, payload.hosts, payload.groups)
        self.audit.record(
            action='inventory.create',
            resource_type='inventory',
            resource_id=str(inventory.id),
            message=f'Inventory {inventory.name} created',
            user_id=user_id,
        )
        self.session.commit()
        return self.get(inventory.id)

    def update(self, inventory_id: UUID, payload: InventoryUpdate, *, user_id: UUID | None = None) -> InventoryRead:
        inventory = self.repository.get(inventory_id)
        if inventory is None:
            raise AppError(404, 'INVENTORY_NOT_FOUND', 'Inventory not found')

        if payload.name and payload.name != inventory.name:
            existing = self.repository.get_by_name(payload.name)
            if existing and existing.id != inventory_id:
                raise AppError(409, 'INVENTORY_EXISTS', 'Inventory name already exists')
            inventory.name = payload.name

        if payload.description is not None:
            inventory.description = payload.description
        if payload.variables is not None:
            inventory.variables_json = payload.variables
        if payload.hosts is not None or payload.groups is not None:
            self.repository.clear_related(inventory)
            self.session.flush()
            self._persist_members(inventory, payload.hosts or [], payload.groups or [])

        self.audit.record(
            action='inventory.update',
            resource_type='inventory',
            resource_id=str(inventory.id),
            message=f'Inventory {inventory.name} updated',
            user_id=user_id,
        )
        self.session.commit()
        return self.get(inventory.id)

    def delete(self, inventory_id: UUID, *, user_id: UUID | None = None) -> None:
        inventory = self.repository.get(inventory_id)
        if inventory is None:
            raise AppError(404, 'INVENTORY_NOT_FOUND', 'Inventory not found')
        self.repository.delete(inventory)
        self.audit.record(
            action='inventory.delete',
            resource_type='inventory',
            resource_id=str(inventory.id),
            message=f'Inventory {inventory.name} deleted',
            user_id=user_id,
        )
        self.session.commit()

    def preview_import(self, *, source_format: ImportFormat, filename: str, raw_bytes: bytes) -> InventoryImportPreview:
        if source_format == ImportFormat.INI:
            preview = self._parse_ini(raw_bytes.decode('utf-8'))
        elif source_format == ImportFormat.YAML:
            preview = self._parse_yaml_inventory(raw_bytes.decode('utf-8'))
        elif source_format == ImportFormat.CSV:
            preview = self._parse_csv(raw_bytes.decode('utf-8'))
        elif source_format == ImportFormat.EXCEL:
            preview = self._parse_excel(raw_bytes)
        else:
            raise AppError(400, 'IMPORT_FORMAT_INVALID', f'Unsupported format {source_format}')

        preview.source_format = source_format
        preview.warnings.append(f'Preview generated from {filename}')
        return preview

    def create_from_preview(self, payload: InventoryImportCommit, *, user_id: UUID | None = None) -> InventoryRead:
        preview = payload.preview
        if self.repository.get_by_name(payload.name):
            raise AppError(409, 'INVENTORY_EXISTS', 'Inventory name already exists')

        inventory = Inventory(
            name=payload.name,
            description=payload.description,
            source_type=InventorySourceType.IMPORT,
            variables_json=preview.variables,
            raw_import=yaml.safe_dump(preview.model_dump(mode='json'), sort_keys=False),
        )
        self.repository.add(inventory)
        self._persist_members(inventory, preview.hosts, preview.groups)
        self.audit.record(
            action='inventory.import',
            resource_type='inventory',
            resource_id=str(inventory.id),
            message=f'Inventory {inventory.name} imported',
            user_id=user_id,
            details={'warnings': preview.warnings},
        )
        self.session.commit()
        return self.get(inventory.id)

    def _persist_members(self, inventory: Inventory, hosts: list[InventoryHostInput], groups: list[InventoryGroupInput]) -> None:
        group_map: dict[str, InventoryGroup] = {}
        for group_payload in groups:
            group = InventoryGroup(
                inventory_id=inventory.id,
                name=group_payload.name,
                description=group_payload.description,
                variables_json=group_payload.variables,
            )
            self.session.add(group)
            self.session.flush()
            group_map[group.name] = group

        for host_payload in hosts:
            host = InventoryHost(
                inventory_id=inventory.id,
                name=host_payload.name,
                address=host_payload.address,
                description=host_payload.description,
                variables_json=host_payload.variables,
                enabled=host_payload.enabled,
            )
            self.session.add(host)
            self.session.flush()
            for group_name in host_payload.groups:
                if group_name not in group_map:
                    group = InventoryGroup(inventory_id=inventory.id, name=group_name, variables_json={})
                    self.session.add(group)
                    self.session.flush()
                    group_map[group_name] = group
                self.session.add(InventoryGroupHost(group_id=group_map[group_name].id, host_id=host.id))

        for group_payload in groups:
            parent = group_map[group_payload.name]
            for child_name in group_payload.children:
                if child_name not in group_map:
                    child = InventoryGroup(inventory_id=inventory.id, name=child_name, variables_json={})
                    self.session.add(child)
                    self.session.flush()
                    group_map[child_name] = child
                self.session.add(InventoryGroupChild(parent_group_id=parent.id, child_group_id=group_map[child_name].id))

    def _serialize(self, inventory: Inventory) -> InventoryRead:
        host_rows = [
            InventoryHostRead(
                id=host.id,
                name=host.name,
                address=host.address,
                description=host.description,
                variables_json=host.variables_json,
                enabled=host.enabled,
                groups=sorted(link.group.name for link in host.group_links),
            )
            for host in inventory.hosts
        ]
        group_rows = [
            InventoryGroupRead(
                id=group.id,
                name=group.name,
                description=group.description,
                variables_json=group.variables_json,
                children=sorted(link.child_group.name for link in group.child_links),
                hosts=sorted(link.host.name for link in group.host_links),
            )
            for group in inventory.groups
        ]
        return InventoryRead(
            id=inventory.id,
            name=inventory.name,
            description=inventory.description,
            source_type=inventory.source_type.value,
            variables_json=inventory.variables_json,
            hosts=host_rows,
            groups=group_rows,
        )

    def _parse_ini(self, text: str) -> InventoryImportPreview:
        hosts: dict[str, NormalizedHost] = {}
        groups: dict[str, NormalizedGroup] = {}
        inventory_vars: dict[str, Any] = {}
        warnings: list[str] = []
        current_section: str | None = None
        section_type = 'group'

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith('#') or line.startswith(';'):
                continue
            if line.startswith('[') and line.endswith(']'):
                section_name = line[1:-1]
                if ':' in section_name:
                    current_section, section_type = section_name.split(':', 1)
                else:
                    current_section, section_type = section_name, 'group'
                if section_type not in {'group', 'vars', 'children'}:
                    warnings.append(f'Unsupported INI section type: {section_name}')
                if current_section not in {'all', 'ungrouped'}:
                    groups.setdefault(current_section, NormalizedGroup(name=current_section))
                continue

            if current_section == 'all' and section_type == 'vars':
                key, value = self._split_assignment(line)
                inventory_vars[key] = value
                continue

            if section_type == 'vars' and current_section:
                key, value = self._split_assignment(line)
                groups.setdefault(current_section, NormalizedGroup(name=current_section)).variables[key] = value
                continue

            if section_type == 'children' and current_section:
                groups.setdefault(current_section, NormalizedGroup(name=current_section)).children.add(line)
                groups.setdefault(line, NormalizedGroup(name=line))
                continue

            try:
                tokens = shlex.split(line)
            except ValueError:
                warnings.append(f'Unable to parse INI line: {line}')
                continue
            if not tokens:
                continue
            host_name = tokens[0]
            host = hosts.setdefault(host_name, NormalizedHost(name=host_name))
            for token in tokens[1:]:
                if '=' not in token:
                    warnings.append(f'Unsupported host token in INI line: {token}')
                    continue
                key, value = token.split('=', 1)
                host.variables[key] = self._coerce_value(value)
                if key == 'ansible_host' and not host.address:
                    host.address = str(host.variables[key])
            if current_section and section_type == 'group' and current_section != 'all':
                host.groups.add(current_section)
            elif current_section is None:
                host.groups.add('ungrouped')
                groups.setdefault('ungrouped', NormalizedGroup(name='ungrouped'))

        return self._build_preview(hosts, groups, inventory_vars, warnings, ImportFormat.INI)

    def _parse_yaml_inventory(self, text: str) -> InventoryImportPreview:
        try:
            payload = yaml.safe_load(text) or {}
        except yaml.YAMLError as exc:
            raise AppError(400, 'INVENTORY_YAML_INVALID', 'Invalid inventory YAML', {'error': str(exc)}) from exc

        hosts: dict[str, NormalizedHost] = {}
        groups: dict[str, NormalizedGroup] = {}
        inventory_vars: dict[str, Any] = {}
        warnings: list[str] = []

        def walk_group(group_name: str, node: dict[str, Any], parent_name: str | None = None) -> None:
            if group_name != 'all':
                groups.setdefault(group_name, NormalizedGroup(name=group_name)).variables.update(node.get('vars') or {})
                if parent_name:
                    groups.setdefault(parent_name, NormalizedGroup(name=parent_name)).children.add(group_name)
            else:
                inventory_vars.update(node.get('vars') or {})

            for host_name, host_vars in (node.get('hosts') or {}).items():
                normalized = hosts.setdefault(host_name, NormalizedHost(name=host_name))
                if isinstance(host_vars, dict):
                    normalized.variables.update(host_vars)
                    normalized.address = normalized.address or host_vars.get('ansible_host')
                if group_name != 'all':
                    normalized.groups.add(group_name)

            for child_name, child_node in (node.get('children') or {}).items():
                if not isinstance(child_node, dict):
                    warnings.append(f'Child group {child_name} is not a mapping and was skipped')
                    continue
                walk_group(child_name, child_node, None if group_name == 'all' else group_name)

        if 'all' in payload and isinstance(payload['all'], dict):
            walk_group('all', payload['all'])
        elif isinstance(payload, dict):
            walk_group('all', {'children': payload})
        else:
            raise AppError(400, 'INVENTORY_YAML_INVALID', 'Inventory YAML must be a mapping')

        return self._build_preview(hosts, groups, inventory_vars, warnings, ImportFormat.YAML)

    def _parse_csv(self, text: str) -> InventoryImportPreview:
        frame = pd.read_csv(io.StringIO(text))
        return self._parse_dataframe(frame, ImportFormat.CSV)

    def _parse_excel(self, raw_bytes: bytes) -> InventoryImportPreview:
        frame = pd.read_excel(io.BytesIO(raw_bytes))
        return self._parse_dataframe(frame, ImportFormat.EXCEL)

    def _parse_dataframe(self, frame: pd.DataFrame, source_format: ImportFormat) -> InventoryImportPreview:
        lowered = {column.lower(): column for column in frame.columns}
        host_column = next((lowered[name] for name in ['name', 'host', 'hostname'] if name in lowered), None)
        if host_column is None:
            raise AppError(400, 'INVENTORY_IMPORT_INVALID', 'CSV/Excel must contain a name, host, or hostname column')
        address_column = next((lowered[name] for name in ['address', 'ansible_host', 'ip'] if name in lowered), None)
        group_column = next((lowered[name] for name in ['groups', 'group'] if name in lowered), None)

        hosts: dict[str, NormalizedHost] = {}
        groups: dict[str, NormalizedGroup] = {}
        warnings: list[str] = []

        for _, row in frame.iterrows():
            host_name = str(row[host_column]).strip()
            if not host_name or host_name.lower() == 'nan':
                warnings.append('Skipped a row without a host name')
                continue
            address = None
            if address_column is not None and pd.notna(row[address_column]):
                address = str(row[address_column]).strip()
            host = hosts.setdefault(host_name, NormalizedHost(name=host_name, address=address))
            if address:
                host.address = address
            for column in frame.columns:
                if column in {host_column, address_column, group_column}:
                    continue
                value = row[column]
                if pd.notna(value):
                    host.variables[column] = value.item() if hasattr(value, 'item') else value
            if group_column is not None and pd.notna(row[group_column]):
                for group_name in [group.strip() for group in str(row[group_column]).split(',') if group.strip()]:
                    host.groups.add(group_name)
                    groups.setdefault(group_name, NormalizedGroup(name=group_name))

        return self._build_preview(hosts, groups, {}, warnings, source_format)

    def _build_preview(
        self,
        hosts: dict[str, NormalizedHost],
        groups: dict[str, NormalizedGroup],
        inventory_vars: dict[str, Any],
        warnings: list[str],
        source_format: ImportFormat,
    ) -> InventoryImportPreview:
        host_items = [
            InventoryHostInput(
                name=host.name,
                address=host.address,
                description=host.description,
                variables=host.variables,
                enabled=host.enabled,
                groups=sorted(host.groups),
            )
            for host in sorted(hosts.values(), key=lambda item: item.name)
        ]
        group_items = [
            InventoryGroupInput(
                name=group.name,
                description=group.description,
                variables=group.variables,
                children=sorted(group.children),
            )
            for group in sorted(groups.values(), key=lambda item: item.name)
        ]
        return InventoryImportPreview(
            source_format=source_format,
            variables=inventory_vars,
            hosts=host_items,
            groups=group_items,
            warnings=warnings,
        )

    def _split_assignment(self, line: str) -> tuple[str, Any]:
        if '=' not in line:
            raise AppError(400, 'INVENTORY_IMPORT_INVALID', f'Expected key=value pair in line: {line}')
        key, value = line.split('=', 1)
        return key.strip(), self._coerce_value(value.strip())

    def _coerce_value(self, value: str) -> Any:
        try:
            return yaml.safe_load(value)
        except yaml.YAMLError:
            return value
