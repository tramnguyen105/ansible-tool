from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID
from zoneinfo import ZoneInfo

from croniter import croniter
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.exceptions import AppError
from app.models.content import Playbook
from app.models.credentials import Credential
from app.models.inventory import Inventory
from app.models.jobs import JobSchedule
from app.modules.audit.service import AuditService
from app.modules.jobs.service import JobService
from app.modules.schedules.repository import ScheduleRepository
from app.modules.schedules.schemas import ScheduleCreate, ScheduleListRead, ScheduleListSummaryRead, ScheduleRead, ScheduleUpdate


class ScheduleService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = ScheduleRepository(session)
        self.audit = AuditService(session)

    def list(self) -> list[ScheduleRead]:
        return [ScheduleRead.model_validate(item) for item in self.repository.list()]

    def list_filtered(
        self,
        *,
        search: str | None = None,
        enabled: bool | None = None,
        mode: str | None = None,
        limit: int = 25,
        offset: int = 0,
        sort_by: str = 'next_run_at',
        sort_order: str = 'asc',
    ) -> ScheduleListRead:
        items, total, summary = self.repository.list_filtered(
            search=search,
            enabled=enabled,
            mode=mode,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        serialized = [ScheduleRead.model_validate(item) for item in items]
        return ScheduleListRead(
            items=serialized,
            total=total,
            limit=limit,
            offset=offset,
            has_more=offset + len(serialized) < total,
            summary=ScheduleListSummaryRead(**summary),
        )

    def get(self, schedule_id: UUID) -> ScheduleRead:
        schedule = self.repository.get(schedule_id)
        if schedule is None:
            raise AppError(404, 'SCHEDULE_NOT_FOUND', 'Schedule not found')
        return ScheduleRead.model_validate(schedule)

    def create(self, payload: ScheduleCreate, *, user_id: UUID | None = None) -> ScheduleRead:
        if self.repository.get_by_name(payload.name):
            raise AppError(409, 'SCHEDULE_EXISTS', 'Schedule name already exists')
        self._validate_targeting(payload.target_type, payload.target_value)
        self._validate_references(payload.inventory_id, payload.credential_id, payload.playbook_id, payload.pre_check_playbook_id, payload.post_check_playbook_id)
        next_run = self.compute_next_run(payload.cron_expression, payload.timezone)
        schedule = JobSchedule(
            name=payload.name,
            description=payload.description,
            cron_expression=payload.cron_expression,
            timezone=payload.timezone,
            enabled=payload.enabled,
            inventory_id=payload.inventory_id,
            credential_id=payload.credential_id,
            playbook_id=payload.playbook_id,
            target_type=payload.target_type,
            target_value=payload.target_value,
            extra_vars_json=payload.extra_vars,
            check_mode=payload.check_mode,
            pre_check_playbook_id=payload.pre_check_playbook_id,
            post_check_playbook_id=payload.post_check_playbook_id,
            pre_check_content=payload.pre_check_content,
            post_check_content=payload.post_check_content,
            next_run_at=next_run,
            created_by_id=user_id,
            updated_by_id=user_id,
        )
        self.repository.add(schedule)
        self.audit.record(
            action='schedule.create',
            resource_type='schedule',
            resource_id=str(schedule.id),
            message=f'Schedule {schedule.name} created',
            user_id=user_id,
            details=self._audit_details(schedule),
        )
        self.session.commit()
        return ScheduleRead.model_validate(schedule)

    def update(self, schedule_id: UUID, payload: ScheduleUpdate, *, user_id: UUID | None = None) -> ScheduleRead:
        schedule = self.repository.get(schedule_id)
        if schedule is None:
            raise AppError(404, 'SCHEDULE_NOT_FOUND', 'Schedule not found')
        if payload.name and payload.name != schedule.name:
            existing = self.repository.get_by_name(payload.name)
            if existing and existing.id != schedule.id:
                raise AppError(409, 'SCHEDULE_EXISTS', 'Schedule name already exists')
            schedule.name = payload.name
        for field_name in ['description', 'cron_expression', 'timezone', 'enabled', 'inventory_id', 'credential_id', 'playbook_id', 'target_type', 'target_value', 'extra_vars', 'check_mode', 'pre_check_playbook_id', 'post_check_playbook_id', 'pre_check_content', 'post_check_content']:
            value = getattr(payload, field_name, None)
            if value is not None:
                if field_name == 'extra_vars':
                    schedule.extra_vars_json = value
                else:
                    setattr(schedule, field_name, value)
        self._validate_targeting(schedule.target_type, schedule.target_value)
        self._validate_references(schedule.inventory_id, schedule.credential_id, schedule.playbook_id, schedule.pre_check_playbook_id, schedule.post_check_playbook_id)
        schedule.next_run_at = self.compute_next_run(schedule.cron_expression, schedule.timezone)
        schedule.updated_by_id = user_id
        self.audit.record(
            action='schedule.update',
            resource_type='schedule',
            resource_id=str(schedule.id),
            message=f'Schedule {schedule.name} updated',
            user_id=user_id,
            details=self._audit_details(schedule),
        )
        self.session.commit()
        return ScheduleRead.model_validate(schedule)

    def delete(self, schedule_id: UUID, *, user_id: UUID | None = None) -> None:
        schedule = self.repository.get(schedule_id)
        if schedule is None:
            raise AppError(404, 'SCHEDULE_NOT_FOUND', 'Schedule not found')
        self.repository.delete(schedule)
        self.audit.record(
            action='schedule.delete',
            resource_type='schedule',
            resource_id=str(schedule.id),
            message=f'Schedule {schedule.name} deleted',
            user_id=user_id,
            details=self._audit_details(schedule),
        )
        self.session.commit()

    def list_due(self, now: datetime | None = None) -> list[JobSchedule]:
        return self.repository.list_due(now or datetime.now(timezone.utc))

    def compute_next_run(self, cron_expression: str, timezone_name: str, base_time: datetime | None = None) -> datetime:
        try:
            tz = ZoneInfo(timezone_name)
        except Exception as exc:
            raise AppError(400, 'SCHEDULE_TIMEZONE_INVALID', 'Invalid schedule timezone', {'error': str(exc)}) from exc
        base = (base_time or datetime.now(timezone.utc)).astimezone(tz)
        try:
            next_local = croniter(cron_expression, base).get_next(datetime)
        except Exception as exc:
            raise AppError(400, 'SCHEDULE_CRON_INVALID', 'Invalid cron expression', {'error': str(exc)}) from exc
        if next_local.tzinfo is None:
            next_local = next_local.replace(tzinfo=tz)
        return next_local.astimezone(timezone.utc)

    def _validate_references(
        self,
        inventory_id: UUID | None,
        credential_id: UUID | None,
        playbook_id: UUID | None,
        pre_check_playbook_id: UUID | None,
        post_check_playbook_id: UUID | None,
    ) -> None:
        if inventory_id and self.session.get(Inventory, inventory_id) is None:
            raise AppError(404, 'INVENTORY_NOT_FOUND', 'Inventory not found')
        if credential_id:
            credential = self.session.get(Credential, credential_id)
            if credential is None:
                raise AppError(404, 'CREDENTIAL_NOT_FOUND', 'Credential not found')
            if not credential.is_active:
                raise AppError(409, 'CREDENTIAL_INACTIVE', 'Credential is inactive')
        if playbook_id and self.session.get(Playbook, playbook_id) is None:
            raise AppError(404, 'PLAYBOOK_NOT_FOUND', 'Playbook not found')
        if pre_check_playbook_id and self.session.get(Playbook, pre_check_playbook_id) is None:
            raise AppError(404, 'PRECHECK_NOT_FOUND', 'Pre-check playbook not found')
        if post_check_playbook_id and self.session.get(Playbook, post_check_playbook_id) is None:
            raise AppError(404, 'POSTCHECK_NOT_FOUND', 'Post-check playbook not found')

    def _validate_targeting(self, target_type: str | None, target_value: str | None) -> None:
        allowed = {'all', 'hosts', 'groups'}
        normalized_type = (target_type or 'all').strip().lower()
        if normalized_type not in allowed:
            raise AppError(400, 'TARGET_TYPE_INVALID', 'Target type must be all, hosts, or groups')
        normalized_value = (target_value or '').strip()
        if normalized_type != 'all' and not normalized_value:
            raise AppError(400, 'TARGET_VALUE_REQUIRED', 'Target value is required when target type is hosts or groups')

    def _audit_details(self, schedule: JobSchedule) -> dict:
        return {
            'inventory_id': str(schedule.inventory_id) if schedule.inventory_id else None,
            'credential_id': str(schedule.credential_id) if schedule.credential_id else None,
            'playbook_id': str(schedule.playbook_id) if schedule.playbook_id else None,
            'target_type': schedule.target_type,
            'target_value': schedule.target_value,
            'check_mode': schedule.check_mode,
            'enabled': schedule.enabled,
            'cron_expression': schedule.cron_expression,
            'timezone': schedule.timezone,
            'next_run_at': schedule.next_run_at.isoformat() if schedule.next_run_at else None,
        }


@celery_app.task(name='app.modules.schedules.service.dispatch_due_schedules')
def dispatch_due_schedules() -> dict:
    session = SessionLocal()
    try:
        service = ScheduleService(session)
        due_schedules = service.list_due()
        dispatched = 0
        skipped = 0
        for schedule in due_schedules:
            try:
                JobService(session).create_from_schedule(schedule, user_id=schedule.created_by_id)
                schedule.last_run_at = datetime.now(timezone.utc)
                schedule.next_run_at = service.compute_next_run(schedule.cron_expression, schedule.timezone, schedule.last_run_at)
                service.audit.record(
                    action='schedule.dispatch',
                    resource_type='schedule',
                    resource_id=str(schedule.id),
                    message=f'Schedule {schedule.name} dispatched a job',
                    user_id=schedule.created_by_id,
                )
                dispatched += 1
            except AppError as exc:
                schedule.enabled = False
                schedule.updated_by_id = schedule.created_by_id
                service.audit.record(
                    action='schedule.auto_disable',
                    resource_type='schedule',
                    resource_id=str(schedule.id),
                    message=f'Schedule {schedule.name} was disabled after failed dispatch dependency validation',
                    user_id=schedule.created_by_id,
                    details={'error': exc.code, 'message': exc.message},
                )
                skipped += 1
        session.commit()
        return {'dispatched': dispatched, 'skipped': skipped}
    finally:
        session.close()
