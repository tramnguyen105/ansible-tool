from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import yaml

from app.celery_app import celery_app
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.jobs import JobStatus
from app.modules.audit.service import AuditService
from app.modules.credentials.service import CredentialService
from app.modules.jobs.repository import JobRepository


settings = get_settings()


def _normalize_inline_playbook(content: str | None) -> str | None:
    if not content:
        return None
    parsed = yaml.safe_load(content)
    if isinstance(parsed, list) and parsed and isinstance(parsed[0], dict) and 'hosts' in parsed[0]:
        return yaml.safe_dump(parsed, sort_keys=False)
    if isinstance(parsed, dict) and 'hosts' in parsed:
        return yaml.safe_dump([parsed], sort_keys=False)
    if isinstance(parsed, dict):
        tasks = [parsed]
    elif isinstance(parsed, list):
        tasks = parsed
    else:
        raise ValueError('Inline pre/post-check content must be a task list or playbook')
    wrapped = [
        {
            'name': 'Inline validation step',
            'hosts': '{{ target_hosts | default("all") }}',
            'gather_facts': False,
            'tasks': tasks,
        }
    ]
    return yaml.safe_dump(wrapped, sort_keys=False)


def _build_inventory_payload(inventory, credential_data: dict[str, str | None], private_key_path: str | None) -> dict:
    all_vars = dict(inventory.variables_json)
    all_vars.setdefault('ansible_connection', 'network_cli')
    all_vars.setdefault('ansible_network_os', 'cisco.ios.ios')
    all_vars.setdefault('ansible_user', credential_data['username'])
    if credential_data.get('password'):
        all_vars.setdefault('ansible_password', credential_data['password'])
    if private_key_path:
        all_vars.setdefault('ansible_ssh_private_key_file', private_key_path)

    payload = {'all': {'vars': all_vars, 'hosts': {}, 'children': {}}}
    for host in inventory.hosts:
        host_vars = dict(host.variables_json)
        if host.address:
            host_vars.setdefault('ansible_host', host.address)
        payload['all']['hosts'][host.name] = host_vars

    group_lookup = {}
    for group in inventory.groups:
        group_payload = {'vars': dict(group.variables_json), 'hosts': {}, 'children': {}}
        for link in group.host_links:
            group_payload['hosts'][link.host.name] = {}
        group_lookup[group.name] = group_payload
    for group in inventory.groups:
        for link in group.child_links:
            group_lookup[group.name]['children'][link.child_group.name] = group_lookup.get(link.child_group.name, {'hosts': {}, 'vars': {}, 'children': {}})
    payload['all']['children'] = group_lookup
    return payload


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')


def _run_ansible(private_data_dir: Path, playbook_name: str, limit: str | None, check_mode: bool) -> dict:
    try:
        import ansible_runner
    except ImportError as exc:
        raise RuntimeError('ansible-runner is not installed in the backend environment') from exc

    cmdline_parts = []
    if limit:
        cmdline_parts.extend(['--limit', limit])
    if check_mode:
        cmdline_parts.append('--check')
    cmdline = ' '.join(cmdline_parts)
    runner = ansible_runner.run(
        private_data_dir=str(private_data_dir),
        playbook=playbook_name,
        cmdline=cmdline,
        quiet=True,
        envvars={'ANSIBLE_HOST_KEY_CHECKING': 'False'},
    )
    stdout_path = Path(getattr(runner, 'artifact_dir', private_data_dir)) / 'stdout'
    stdout = stdout_path.read_text(encoding='utf-8') if stdout_path.exists() else ''
    return {
        'status': getattr(runner, 'status', 'unknown'),
        'rc': getattr(runner, 'rc', None),
        'stats': getattr(runner, 'stats', {}) or {},
        'artifact_dir': getattr(runner, 'artifact_dir', None),
        'stdout': stdout,
    }


@celery_app.task(name='app.modules.jobs.tasks.execute_job')
def execute_job(job_id: str) -> dict:
    session = SessionLocal()
    repository = JobRepository(session)
    audit = AuditService(session)
    try:
        job = repository.get_for_execution(UUID(job_id))
        if job is None:
            return {'error': 'Job not found'}
        if job.inventory is None or job.credential is None or job.playbook is None:
            raise RuntimeError('Job is missing inventory, credential, or playbook')

        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(timezone.utc)
        result = repository.ensure_result(job)
        session.commit()

        credential_data = CredentialService(session).resolve_for_execution(
            job.credential_id,
            user_id=job.requested_by_id,
            job_id=str(job.id),
        )

        private_data_dir = settings.runner_data_path / str(job.id)
        inventory_path = private_data_dir / 'inventory' / 'hosts.yml'
        project_dir = private_data_dir / 'project'
        env_dir = private_data_dir / 'env'
        project_dir.mkdir(parents=True, exist_ok=True)
        env_dir.mkdir(parents=True, exist_ok=True)

        private_key_path = None
        if credential_data.get('private_key'):
            key_path = env_dir / 'id_rsa'
            key_path.write_text(credential_data['private_key'], encoding='utf-8')
            private_key_path = str(key_path)
        if credential_data.get('passphrase'):
            (env_dir / 'passwords').write_text(
                json.dumps({'Enter passphrase for .*:': credential_data['passphrase']}),
                encoding='utf-8',
            )

        inventory_payload = _build_inventory_payload(job.inventory, credential_data, private_key_path)
        _write_file(inventory_path, yaml.safe_dump(inventory_payload, sort_keys=False))
        _write_file(private_data_dir / 'env' / 'extravars', yaml.safe_dump(job.extra_vars_json, sort_keys=False))

        limit = job.target_value if job.target_type in {'hosts', 'groups'} else None
        step_outputs: list[dict] = []
        steps = []
        if job.pre_check_playbook is not None:
            steps.append(('pre_check', job.pre_check_playbook.yaml_content, False))
        elif job.pre_check_content:
            steps.append(('pre_check', _normalize_inline_playbook(job.pre_check_content), False))
        steps.append(('main', job.playbook.yaml_content, job.check_mode))
        if job.post_check_playbook is not None:
            steps.append(('post_check', job.post_check_playbook.yaml_content, False))
        elif job.post_check_content:
            steps.append(('post_check', _normalize_inline_playbook(job.post_check_content), False))

        final_rc = 0
        for step_name, playbook_content, check_mode in steps:
            playbook_name = f'{step_name}.yml'
            _write_file(project_dir / playbook_name, playbook_content or '')
            run_result = _run_ansible(private_data_dir, playbook_name, limit, check_mode)
            step_outputs.append({'step': step_name, **run_result})
            if run_result['rc'] not in (0, None):
                final_rc = run_result['rc']
                break

        result.return_code = final_rc
        result.stdout = '\n\n'.join(output['stdout'] for output in step_outputs if output.get('stdout'))
        result.stderr = '' if final_rc == 0 else 'One or more execution steps failed'
        result.summary_json = {'steps': step_outputs, 'final_rc': final_rc}
        result.artifact_dir = str(private_data_dir)
        job.status = JobStatus.SUCCESS if final_rc == 0 else JobStatus.FAILED
        job.finished_at = datetime.now(timezone.utc)
        audit.record(
            action='job.execute',
            resource_type='job',
            resource_id=str(job.id),
            message=f'Job {job.name} finished with status {job.status.value}',
            user_id=job.requested_by_id,
            status='success' if job.status == JobStatus.SUCCESS else 'failure',
            details={'final_rc': final_rc},
        )
        session.commit()
        return {'job_id': str(job.id), 'status': job.status.value, 'final_rc': final_rc}
    except Exception as exc:  # pragma: no cover - defensive runtime path
        session.rollback()
        job = repository.get_for_execution(UUID(job_id))
        if job is not None:
            result = repository.ensure_result(job)
            result.stderr = str(exc)
            job.status = JobStatus.FAILED
            job.finished_at = datetime.now(timezone.utc)
            audit.record(
                action='job.execute',
                resource_type='job',
                resource_id=str(job.id),
                message=f'Job {job.name} failed',
                user_id=job.requested_by_id,
                status='failure',
                details={'error': str(exc)},
            )
            session.commit()
        return {'job_id': job_id, 'status': 'failed', 'error': str(exc)}
    finally:
        session.close()
