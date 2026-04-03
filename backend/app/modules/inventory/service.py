from __future__ import annotations

import io
import json
import shlex
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any
from uuid import uuid4
from uuid import UUID

import pandas as pd
import yaml
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models.inventory import Inventory, InventoryGroup, InventoryGroupChild, InventoryGroupHost, InventoryHost, InventorySourceType
from app.models.jobs import Job, JobSchedule, JobStatus
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
    InventoryImportPreviewRead,
    InventoryRead,
    InventorySummaryStatsRead,
    InventorySummaryListRead,
    InventorySummaryRead,
    InventoryUpdate,
    InventoryUsageRead,
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

_PREVIEW_TTL_MINUTES = 10
_READINESS_VALUES = {'ready', 'incomplete', 'disabled', 'review'}


class InventoryService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = InventoryRepository(session)
        self.audit = AuditService(session)

    def list(self) -> list[InventoryRead]:
        return [self._serialize(item) for item in self.repository.list()]

    def list_summary(self) -> list[InventorySummaryRead]:
        return [self._build_summary(item) for item in self.repository.list_summary()]

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
    ) -> InventorySummaryListRead:
        self._validate_source_types(source_types)
        self._validate_readiness(readiness)
        items, total, stats = self.repository.list_summary_filtered(
            search=search,
            source_types=source_types,
            readiness=readiness,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        serialized = [self._build_summary(item) for item in items]
        return InventorySummaryListRead(
            items=serialized,
            total=total,
            limit=limit,
            offset=offset,
            has_more=offset + len(serialized) < total,
            stats=InventorySummaryStatsRead(**stats),
        )

    def get(self, inventory_id: UUID) -> InventoryRead:
        inventory = self.repository.get(inventory_id)
        if inventory is None:
            raise AppError(404, 'INVENTORY_NOT_FOUND', 'Inventory not found')
        return self._serialize(inventory)

    def usage(self, inventory_id: UUID) -> InventoryUsageRead:
        inventory = self.repository.get(inventory_id)
        if inventory is None:
            raise AppError(404, 'INVENTORY_NOT_FOUND', 'Inventory not found')

        schedules_total = self.session.scalar(select(func.count(JobSchedule.id)).where(JobSchedule.inventory_id == inventory_id)) or 0
        schedules_enabled = self.session.scalar(
            select(func.count(JobSchedule.id)).where(JobSchedule.inventory_id == inventory_id, JobSchedule.enabled.is_(True))
        ) or 0
        jobs_total = self.session.scalar(select(func.count(Job.id)).where(Job.inventory_id == inventory_id)) or 0
        jobs_active = self.session.scalar(
            select(func.count(Job.id)).where(Job.inventory_id == inventory_id, Job.status.in_([JobStatus.PENDING, JobStatus.QUEUED, JobStatus.RUNNING]))
        ) or 0
        return InventoryUsageRead(
            schedules_total=int(schedules_total),
            schedules_enabled=int(schedules_enabled),
            jobs_total=int(jobs_total),
            jobs_active=int(jobs_active),
        )

    def create(self, payload: InventoryCreate, *, user_id: UUID | None = None) -> InventoryRead:
        if self.repository.get_by_name(payload.name):
            raise AppError(409, 'INVENTORY_EXISTS', 'Inventory name already exists')
        self._validate_member_payload(payload.hosts, payload.groups)

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
            self._validate_member_payload(payload.hosts or [], payload.groups or [])
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
        usage = self.usage(inventory_id)
        if usage.schedules_enabled > 0:
            raise AppError(
                409,
                'INVENTORY_IN_USE',
                'Inventory is still referenced by enabled schedules',
                details=usage.model_dump(),
            )
        if usage.jobs_active > 0:
            raise AppError(
                409,
                'INVENTORY_IN_USE',
                'Inventory is referenced by active jobs',
                details=usage.model_dump(),
            )
        self.repository.delete(inventory)
        self.audit.record(
            action='inventory.delete',
            resource_type='inventory',
            resource_id=str(inventory.id),
            message=f'Inventory {inventory.name} deleted',
            user_id=user_id,
        )
        self.session.commit()

    def preview_import(self, *, source_format: ImportFormat, filename: str, raw_bytes: bytes) -> InventoryImportPreviewRead:
        self._validate_upload(filename=filename, raw_bytes=raw_bytes, source_format=source_format)
        try:
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
        except UnicodeDecodeError as exc:
            raise AppError(400, 'INVENTORY_IMPORT_INVALID', 'Text-based imports must be UTF-8 encoded', {'error': str(exc)}) from exc

        preview.source_format = source_format
        preview.warnings.append(f'Preview generated from {filename}')
        stored_preview = self._store_preview(preview)
        self.session.commit()
        return stored_preview

    def create_from_preview(self, payload: InventoryImportCommit, *, user_id: UUID | None = None) -> InventoryRead:
        preview = self._resolve_preview(payload.preview_id, payload.checksum)
        if self.repository.get_by_name(payload.name):
            raise AppError(409, 'INVENTORY_EXISTS', 'Inventory name already exists')
        self._validate_member_payload(preview.hosts, preview.groups)

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
        self._drop_preview(payload.preview_id)
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

    def _validate_member_payload(self, hosts: list[InventoryHostInput], groups: list[InventoryGroupInput]) -> None:
        seen_hosts: set[str] = set()
        for host in hosts:
            key = host.name.strip().lower()
            if key in seen_hosts:
                raise AppError(400, 'INVENTORY_HOST_DUPLICATE', f'Duplicate host name: {host.name}')
            seen_hosts.add(key)

        seen_groups: set[str] = set()
        adjacency: dict[str, set[str]] = {}
        for group in groups:
            parent = group.name.strip()
            group_key = parent.lower()
            if group_key in seen_groups:
                raise AppError(400, 'INVENTORY_GROUP_DUPLICATE', f'Duplicate group name: {group.name}')
            seen_groups.add(group_key)
            adjacency.setdefault(parent, set())
            for child in group.children:
                child_name = child.strip()
                if not child_name:
                    continue
                if child_name == parent:
                    raise AppError(400, 'INVENTORY_GROUP_INVALID', f'Group "{parent}" cannot include itself as a child')
                adjacency[parent].add(child_name)
                adjacency.setdefault(child_name, set())

        state: dict[str, int] = {}

        def dfs(node: str, stack: list[str]) -> None:
            state[node] = 1
            stack.append(node)
            for child in adjacency.get(node, set()):
                child_state = state.get(child, 0)
                if child_state == 1:
                    cycle = ' -> '.join(stack + [child])
                    raise AppError(400, 'INVENTORY_GROUP_CYCLE', f'Group hierarchy contains a cycle: {cycle}')
                if child_state == 0:
                    dfs(child, stack)
            stack.pop()
            state[node] = 2

        for node in adjacency:
            if state.get(node, 0) == 0:
                dfs(node, [])

    def _build_summary(self, inventory: dict[str, Any]) -> InventorySummaryRead:
        host_count = int(inventory['host_count'])
        enabled_host_count = int(inventory['enabled_host_count'])
        group_count = int(inventory['group_count'])
        variable_scope_count = int(inventory['group_variable_scope_count']) + (1 if inventory['has_inventory_vars'] else 0)

        readiness = 'review'
        readiness_note = 'Inventory exists but needs more context.'
        if host_count and enabled_host_count:
            readiness = 'ready'
            readiness_note = 'Usable for operator targeting.'
        if not host_count:
            readiness = 'incomplete'
            readiness_note = 'No hosts are assigned yet.'
        if host_count and not enabled_host_count:
            readiness = 'disabled'
            readiness_note = 'All hosts are currently disabled.'

        return InventorySummaryRead(
            id=inventory['id'],
            name=inventory['name'],
            description=inventory['description'],
            source_type=inventory['source_type'],
            host_count=host_count,
            enabled_host_count=enabled_host_count,
            group_count=group_count,
            variable_scope_count=variable_scope_count,
            readiness=readiness,
            readiness_note=readiness_note,
        )

    def _store_preview(self, preview: InventoryImportPreview) -> InventoryImportPreviewRead:
        preview_payload = preview.model_dump(mode='json')
        preview_json = json.dumps(preview_payload, sort_keys=True, default=str)
        preview_id = str(uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=_PREVIEW_TTL_MINUTES)
        checksum = sha256(preview_json.encode('utf-8')).hexdigest()
        self._purge_previews()
        self.repository.add_preview_token(
            preview_id=preview_id,
            checksum=checksum,
            expires_at=expires_at,
            payload_json=preview_payload,
        )
        return InventoryImportPreviewRead(
            preview_id=preview_id,
            checksum=checksum,
            expires_at=expires_at.isoformat(),
            preview=preview,
        )

    def _resolve_preview(self, preview_id: str, checksum: str) -> InventoryImportPreview:
        self._purge_previews()
        token = self.repository.get_preview_token(preview_id)
        if token is None:
            raise AppError(400, 'INVENTORY_PREVIEW_EXPIRED', 'Preview token is invalid or expired. Generate a new preview.')
        if token.checksum != checksum:
            raise AppError(400, 'INVENTORY_PREVIEW_TAMPERED', 'Preview payload checksum mismatch. Generate a new preview.')
        if token.expires_at < datetime.now(timezone.utc):
            self.repository.delete_preview_token(token)
            self.session.commit()
            raise AppError(400, 'INVENTORY_PREVIEW_EXPIRED', 'Preview token is invalid or expired. Generate a new preview.')
        return InventoryImportPreview.model_validate(token.payload_json)

    def _drop_preview(self, preview_id: str) -> None:
        token = self.repository.get_preview_token(preview_id)
        if token is not None:
            self.repository.delete_preview_token(token)

    def _purge_previews(self) -> None:
        self.repository.purge_expired_preview_tokens(now=datetime.now(timezone.utc))

    def _validate_upload(self, *, filename: str, raw_bytes: bytes, source_format: ImportFormat) -> None:
        if not raw_bytes:
            raise AppError(400, 'INVENTORY_IMPORT_INVALID', 'Uploaded file is empty')
        if len(raw_bytes) > 5 * 1024 * 1024:
            raise AppError(413, 'INVENTORY_IMPORT_TOO_LARGE', 'Uploaded file exceeds the 5 MB limit')

        lowered = filename.lower()
        allowed_extensions = {
            ImportFormat.INI: ('.ini',),
            ImportFormat.YAML: ('.yml', '.yaml'),
            ImportFormat.CSV: ('.csv',),
            ImportFormat.EXCEL: ('.xls', '.xlsx'),
        }
        if filename and not lowered.endswith(allowed_extensions[source_format]):
            raise AppError(
                400,
                'INVENTORY_IMPORT_TYPE_MISMATCH',
                f'File extension does not match selected format "{source_format}"',
            )

    def _validate_source_types(self, source_types: list[str] | None) -> None:
        if not source_types:
            return
        allowed = {source.value for source in InventorySourceType}
        invalid = sorted({item for item in source_types if item not in allowed})
        if invalid:
            raise AppError(
                400,
                'INVENTORY_SOURCE_TYPE_INVALID',
                'One or more inventory source types are invalid',
                {'invalid_values': invalid, 'allowed_values': sorted(allowed)},
            )

    def _validate_readiness(self, readiness: list[str] | None) -> None:
        if not readiness:
            return
        invalid = sorted({item for item in readiness if item not in _READINESS_VALUES})
        if invalid:
            raise AppError(
                400,
                'INVENTORY_READINESS_INVALID',
                'One or more readiness filters are invalid',
                {'invalid_values': invalid, 'allowed_values': sorted(_READINESS_VALUES)},
            )

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
        try:
            frame = pd.read_csv(io.StringIO(text))
        except Exception as exc:
            raise AppError(400, 'INVENTORY_IMPORT_INVALID', 'CSV could not be parsed', {'error': str(exc)}) from exc
        return self._parse_dataframe(frame, ImportFormat.CSV)

    def _parse_excel(self, raw_bytes: bytes) -> InventoryImportPreview:
        try:
            frame = pd.read_excel(io.BytesIO(raw_bytes))
        except Exception as exc:
            raise AppError(400, 'INVENTORY_IMPORT_INVALID', 'Excel file could not be parsed', {'error': str(exc)}) from exc
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

        host_column_name = str(host_column) if host_column is not None else ''
        address_column_name = str(address_column) if address_column is not None else ''
        group_column_name = str(group_column) if group_column is not None else ''
        inferred_columns = [str(column) for column in frame.columns if str(column) not in {host_column_name, address_column_name, group_column_name}]
        preview = self._build_preview(hosts, groups, {}, warnings, source_format)
        preview.metadata = {
            'row_count': int(frame.shape[0]),
            'host_column': host_column_name,
            'address_column': address_column_name,
            'group_column': group_column_name,
            'inferred_variable_columns': inferred_columns,
        }
        return preview

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
