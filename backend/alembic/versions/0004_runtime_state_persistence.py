"""persist runtime state tables

Revision ID: 0004_runtime_state_persistence
Revises: 0003_settings_domains
Create Date: 2026-04-02 05:15:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = '0004_runtime_state_persistence'
down_revision = '0003_settings_domains'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'auth_login_throttles',
        sa.Column('subject_key', sa.String(length=255), nullable=False),
        sa.Column('attempt_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('window_started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_attempt_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_auth_login_throttles')),
        sa.UniqueConstraint('subject_key', name='uq_auth_login_throttles_subject_key'),
    )
    op.create_index(op.f('ix_auth_login_throttles_subject_key'), 'auth_login_throttles', ['subject_key'], unique=False)

    op.create_table(
        'inventory_import_preview_tokens',
        sa.Column('preview_id', sa.String(length=64), nullable=False),
        sa.Column('checksum', sa.String(length=64), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('payload_json', sa.JSON(), nullable=False),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_inventory_import_preview_tokens')),
        sa.UniqueConstraint('preview_id', name='uq_inventory_import_preview_tokens_preview_id'),
    )
    op.create_index(op.f('ix_inventory_import_preview_tokens_expires_at'), 'inventory_import_preview_tokens', ['expires_at'], unique=False)
    op.create_index(op.f('ix_inventory_import_preview_tokens_preview_id'), 'inventory_import_preview_tokens', ['preview_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_inventory_import_preview_tokens_preview_id'), table_name='inventory_import_preview_tokens')
    op.drop_index(op.f('ix_inventory_import_preview_tokens_expires_at'), table_name='inventory_import_preview_tokens')
    op.drop_table('inventory_import_preview_tokens')
    op.drop_index(op.f('ix_auth_login_throttles_subject_key'), table_name='auth_login_throttles')
    op.drop_table('auth_login_throttles')
