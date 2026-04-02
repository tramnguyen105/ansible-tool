from __future__ import annotations

from typing import Any
from uuid import UUID

import yaml
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models.content import CliConversionJob
from app.modules.cli_converter.schemas import (
    CliBlock,
    CliConversionJobRead,
    CliGenerateResult,
    CliOutputType,
    CliParseResult,
    CliWarning,
    CliSavePlaybookRequest,
    CliSaveTemplateRequest,
    CliValidateGeneratedResult,
)
from app.modules.playbooks.schemas import PlaybookCreate
from app.modules.playbooks.service import PlaybookService
from app.modules.templates.schemas import TemplateCreate, TemplateSourceTypeSchema
from app.modules.templates.service import TemplateService


SUPPORTED_PREFIXES = {
    'interface ': 'interface',
    'line ': 'line',
    'router ': 'router',
    'vlan ': 'vlan',
}


class CliConverterService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def parse(self, config_text: str) -> CliParseResult:
        global_lines: list[str] = []
        blocks: list[CliBlock] = []
        warnings: list[CliWarning] = []
        raw_lines = config_text.splitlines()
        index = 0

        while index < len(raw_lines):
            raw_line = raw_lines[index].rstrip()
            stripped = raw_line.strip()
            current_line = index + 1
            index += 1
            if not stripped or stripped == '!':
                continue
            if raw_line.startswith(' '):
                warnings.append(
                    CliWarning(
                        code='ORPHANED_INDENT',
                        message=f'Orphaned indented line treated as unsupported global line: {stripped}',
                        line=current_line,
                    )
                )
                global_lines.append(stripped)
                continue

            child_lines: list[str] = []
            while index < len(raw_lines):
                candidate = raw_lines[index].rstrip('\n')
                candidate_stripped = candidate.strip()
                if not candidate_stripped or candidate_stripped == '!':
                    index += 1
                    continue
                if candidate.startswith(' '):
                    child_lines.append(candidate.strip())
                    index += 1
                else:
                    break

            if not child_lines:
                global_lines.append(stripped)
                continue

            kind = next((value for prefix, value in SUPPORTED_PREFIXES.items() if stripped.startswith(prefix)), None)
            if kind is None:
                warnings.append(
                    CliWarning(
                        code='UNSUPPORTED_BLOCK',
                        message=f'Unsupported parent block retained as warning only: {stripped}',
                        line=current_line,
                    )
                )
                blocks.append(CliBlock(kind='unsupported', parent=stripped, lines=child_lines, line=current_line, supported=False))
            else:
                blocks.append(CliBlock(kind=kind, parent=stripped, lines=child_lines, line=current_line, supported=True))

        return CliParseResult(global_lines=global_lines, blocks=blocks, warnings=warnings)

    def validate(self, config_text: str) -> dict[str, Any]:
        parsed = self.parse(config_text)
        return {'valid': True, 'warnings': parsed.warnings}

    def validate_generated(self, output_type: CliOutputType, generated_content: str) -> CliValidateGeneratedResult:
        if output_type == CliOutputType.TEMPLATE:
            try:
                TemplateService(self.session).validate_content(generated_content)
                return CliValidateGeneratedResult(valid=True, normalized_content=generated_content, errors=[])
            except AppError as exc:
                return CliValidateGeneratedResult(valid=False, errors=[exc.message], normalized_content=None)
        normalized = self._normalize_generated_playbook(output_type, generated_content)
        validation = PlaybookService(self.session).validate_yaml(normalized)
        return CliValidateGeneratedResult(valid=validation.valid, errors=validation.errors, normalized_content=normalized if validation.valid else None)

    def generate(
        self,
        config_text: str,
        output_type: CliOutputType,
        *,
        user_id: UUID | None = None,
        parsed: CliParseResult | None = None,
    ) -> CliGenerateResult:
        parsed_result = parsed or self.parse(config_text)
        if output_type == CliOutputType.TEMPLATE:
            generated = self._build_template(parsed_result)
        elif output_type == CliOutputType.TASKS:
            generated = self._build_tasks_yaml(parsed_result)
        elif output_type == CliOutputType.PLAYBOOK:
            generated = self._build_playbook_yaml(parsed_result)
        else:
            raise AppError(400, 'CLI_OUTPUT_INVALID', 'Unsupported output type')

        conversion = CliConversionJob(
            output_type=output_type.value,
            input_config=config_text,
            parsed_json=parsed_result.model_dump(mode='json'),
            generated_content=generated,
            warnings_json=parsed_result.warnings,
            created_by_id=user_id,
        )
        self.session.add(conversion)
        self.session.commit()
        return CliGenerateResult(
            output_type=output_type,
            parsed=parsed_result,
            generated_content=generated,
            warnings=parsed_result.warnings,
            conversion_job_id=conversion.id,
        )

    def save_as_playbook(self, payload: CliSavePlaybookRequest, *, user_id: UUID | None = None):
        normalized_content = self._normalize_generated_playbook(payload.output_type, payload.generated_content)
        note_suffix = f' (conversion_job_id={payload.conversion_job_id})' if payload.conversion_job_id else ''
        playbook = PlaybookService(self.session).create(
            PlaybookCreate(
                name=payload.name,
                description=payload.description,
                yaml_content=normalized_content,
                is_generated=True,
                change_note=f'Saved from CLI converter ({payload.output_type.value}){note_suffix}',
            ),
            user_id=user_id,
        )
        return playbook

    def save_as_template(self, payload: CliSaveTemplateRequest, *, user_id: UUID | None = None):
        template = TemplateService(self.session).create(
            TemplateCreate(name=payload.name, description=payload.description, content=payload.generated_content),
            user_id=user_id,
            source_type=TemplateSourceTypeSchema.CONVERTER,
            conversion_job_id=payload.conversion_job_id,
        )
        return template

    def list_history(self, *, limit: int = 20) -> list[CliConversionJobRead]:
        safe_limit = min(max(limit, 1), 100)
        rows = self.session.scalars(select(CliConversionJob).order_by(desc(CliConversionJob.created_at)).limit(safe_limit)).all()
        return [
            CliConversionJobRead(
                id=item.id,
                output_type=CliOutputType(item.output_type),
                warning_count=len(item.warnings_json or []),
                created_at=item.created_at,
            )
            for item in rows
        ]

    def _build_template(self, parsed: CliParseResult) -> str:
        blocks_by_kind: dict[str, list[dict[str, Any]]] = {'interface': [], 'line': [], 'router': [], 'vlan': []}
        for block in parsed.blocks:
            if block.supported and block.kind in blocks_by_kind:
                blocks_by_kind[block.kind].append({'name': block.parent.split(' ', 1)[1], 'lines': block.lines})

        sections = [
            '{% for line in global_config %}',
            '{{ line }}',
            '{% endfor %}',
            '',
            '{% for item in interface_blocks %}',
            'interface {{ item.name }}',
            '{% for line in item.lines %}',
            ' {{ line }}',
            '{% endfor %}',
            '{% endfor %}',
            '',
            '{% for item in line_blocks %}',
            'line {{ item.name }}',
            '{% for line in item.lines %}',
            ' {{ line }}',
            '{% endfor %}',
            '{% endfor %}',
            '',
            '{% for item in router_blocks %}',
            'router {{ item.name }}',
            '{% for line in item.lines %}',
            ' {{ line }}',
            '{% endfor %}',
            '{% endfor %}',
            '',
            '{% for item in vlan_blocks %}',
            'vlan {{ item.name }}',
            '{% for line in item.lines %}',
            ' {{ line }}',
            '{% endfor %}',
            '{% endfor %}',
            '',
            '{# Suggested variables #}',
            '{# global_config = ' + yaml.safe_dump(parsed.global_lines, default_flow_style=False).strip() + ' #}',
            '{# interface_blocks = ' + yaml.safe_dump(blocks_by_kind['interface'], sort_keys=False).strip() + ' #}',
            '{# line_blocks = ' + yaml.safe_dump(blocks_by_kind['line'], sort_keys=False).strip() + ' #}',
            '{# router_blocks = ' + yaml.safe_dump(blocks_by_kind['router'], sort_keys=False).strip() + ' #}',
            '{# vlan_blocks = ' + yaml.safe_dump(blocks_by_kind['vlan'], sort_keys=False).strip() + ' #}',
        ]
        return '\n'.join(sections).strip() + '\n'

    def _build_tasks_yaml(self, parsed: CliParseResult) -> str:
        tasks: list[dict[str, Any]] = []
        supported_blocks = [block for block in parsed.blocks if block.supported]
        if parsed.global_lines:
            tasks.append(
                {
                    'name': 'Apply global Cisco IOS configuration',
                    'cisco.ios.ios_config': {
                        'lines': parsed.global_lines,
                    },
                }
            )
        for block in supported_blocks:
            tasks.append(
                {
                    'name': f'Apply {block.kind} block {block.parent}',
                    'cisco.ios.ios_config': {
                        'parents': [block.parent],
                        'lines': block.lines,
                    },
                }
            )
        return yaml.safe_dump(tasks, sort_keys=False)

    def _build_playbook_yaml(self, parsed: CliParseResult) -> str:
        tasks = yaml.safe_load(self._build_tasks_yaml(parsed))
        playbook = [
            {
                'name': 'Apply Cisco IOS generated configuration',
                'hosts': '{{ target_hosts | default("all") }}',
                'gather_facts': False,
                'collections': ['cisco.ios'],
                'tasks': tasks,
            }
        ]
        return yaml.safe_dump(playbook, sort_keys=False)

    def _normalize_generated_playbook(self, output_type: CliOutputType, generated_content: str) -> str:
        if output_type == CliOutputType.PLAYBOOK:
            return generated_content
        if output_type == CliOutputType.TASKS:
            parsed = yaml.safe_load(generated_content)
            if isinstance(parsed, list) and parsed and isinstance(parsed[0], dict) and 'hosts' in parsed[0]:
                return yaml.safe_dump(parsed, sort_keys=False)
            if isinstance(parsed, dict):
                tasks = [parsed]
            elif isinstance(parsed, list):
                tasks = parsed
            else:
                raise AppError(400, 'CLI_TASKS_INVALID', 'Generated tasks must be a YAML list or mapping')
            wrapped = [
                {
                    'name': 'Apply Cisco IOS generated configuration',
                    'hosts': '{{ target_hosts | default("all") }}',
                    'gather_facts': False,
                    'collections': ['cisco.ios'],
                    'tasks': tasks,
                }
            ]
            return yaml.safe_dump(wrapped, sort_keys=False)
        raise AppError(400, 'CLI_OUTPUT_INVALID', 'Unsupported output type for playbook save')
