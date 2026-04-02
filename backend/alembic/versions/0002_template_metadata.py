"""add template metadata and provenance

Revision ID: 0002_template_metadata
Revises: 0001_initial
Create Date: 2026-04-01 12:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = '0002_template_metadata'
down_revision = '0001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('templates', sa.Column('source_type', sa.String(length=32), server_default='manual', nullable=False))
    op.add_column('templates', sa.Column('conversion_job_id', sa.Uuid(), nullable=True))
    op.add_column('templates', sa.Column('content_hash', sa.String(length=64), server_default='', nullable=False))
    op.add_column('templates', sa.Column('revision', sa.Integer(), server_default='1', nullable=False))
    op.create_index(op.f('ix_templates_source_type'), 'templates', ['source_type'], unique=False)
    op.create_foreign_key(
        op.f('fk_templates_conversion_job_id_cli_conversion_jobs'),
        'templates',
        'cli_conversion_jobs',
        ['conversion_job_id'],
        ['id'],
        ondelete='SET NULL',
    )

    op.execute("UPDATE templates SET content_hash = md5(content), revision = 1, source_type = 'manual' WHERE content_hash = '' OR content_hash IS NULL")
    op.alter_column('templates', 'source_type', server_default=None)
    op.alter_column('templates', 'content_hash', server_default=None)
    op.alter_column('templates', 'revision', server_default=None)


def downgrade() -> None:
    op.drop_constraint(op.f('fk_templates_conversion_job_id_cli_conversion_jobs'), 'templates', type_='foreignkey')
    op.drop_index(op.f('ix_templates_source_type'), table_name='templates')
    op.drop_column('templates', 'revision')
    op.drop_column('templates', 'content_hash')
    op.drop_column('templates', 'conversion_job_id')
    op.drop_column('templates', 'source_type')
