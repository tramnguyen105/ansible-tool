"""add settings domain tables

Revision ID: 0003_settings_domains
Revises: 0002_template_metadata
Create Date: 2026-04-02 03:45:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = '0003_settings_domains'
down_revision = '0002_template_metadata'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'system_configuration',
        sa.Column('singleton_key', sa.String(length=32), nullable=False),
        sa.Column('ldap_enabled', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('ldap_server_uri', sa.String(length=255), nullable=False, server_default='ldap://ldap.example.internal'),
        sa.Column('ldap_use_ssl', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('ldap_bind_dn', sa.String(length=255), nullable=True),
        sa.Column('ldap_search_base', sa.String(length=255), nullable=True),
        sa.Column('ldap_search_filter', sa.String(length=255), nullable=False, server_default='(sAMAccountName={username})'),
        sa.Column('ldap_username_attribute', sa.String(length=64), nullable=False, server_default='sAMAccountName'),
        sa.Column('ldap_user_dn_template', sa.String(length=255), nullable=True),
        sa.Column('allow_local_auth', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('password_reset_enabled', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('password_reset_token_ttl_minutes', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('password_min_length', sa.Integer(), nullable=False, server_default='12'),
        sa.Column('password_require_special', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('snmp_enabled', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('snmp_version', sa.String(length=16), nullable=False, server_default='v2c'),
        sa.Column('snmp_default_port', sa.Integer(), nullable=False, server_default='161'),
        sa.Column('snmp_timeout_seconds', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('snmp_retries', sa.Integer(), nullable=False, server_default='2'),
        sa.Column('snmp_trap_target', sa.String(length=255), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_system_configuration')),
        sa.UniqueConstraint('singleton_key', name='uq_system_configuration_singleton_key'),
    )

    op.create_table(
        'user_preferences',
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('timezone', sa.String(length=64), nullable=False, server_default='UTC'),
        sa.Column('date_format', sa.String(length=32), nullable=False, server_default='YYYY-MM-DD'),
        sa.Column('time_format', sa.String(length=16), nullable=False, server_default='24h'),
        sa.Column('auto_refresh_seconds', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('show_relative_time', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_user_preferences_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_user_preferences')),
        sa.UniqueConstraint('user_id', name='uq_user_preferences_user_id'),
    )
    op.create_index(op.f('ix_user_preferences_user_id'), 'user_preferences', ['user_id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_user_preferences_user_id'), table_name='user_preferences')
    op.drop_table('user_preferences')
    op.drop_table('system_configuration')
