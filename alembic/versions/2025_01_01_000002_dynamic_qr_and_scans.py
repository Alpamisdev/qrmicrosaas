"""dynamic qr and scans tables

Revision ID: dynamic_qr_scans_0002
Revises: add_users_table_0001
Create Date: 2025-01-01 00:10:00

"""
from alembic import op
import sqlalchemy as sa


revision = 'dynamic_qr_scans_0002'
down_revision = 'add_users_table_0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    existing_tables = set(inspector.get_table_names())

    # dynamic_qr table (create if missing)
    if 'dynamic_qr' not in existing_tables:
        op.create_table(
            'dynamic_qr',
            sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('short_code', sa.String(length=20), nullable=False),
            sa.Column('destination_url', sa.Text(), nullable=False),
            sa.Column('title', sa.String(length=200), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        )
        # indexes
        op.create_index('ix_dynamic_qr_user_id', 'dynamic_qr', ['user_id'])
        op.create_index('ix_dynamic_qr_short_code', 'dynamic_qr', ['short_code'], unique=True)
    else:
        # ensure indexes exist
        idx_names = {idx['name'] for idx in inspector.get_indexes('dynamic_qr')}
        if 'ix_dynamic_qr_user_id' not in idx_names:
            try:
                op.create_index('ix_dynamic_qr_user_id', 'dynamic_qr', ['user_id'])
            except Exception:
                pass
        if 'ix_dynamic_qr_short_code' not in idx_names:
            try:
                op.create_index('ix_dynamic_qr_short_code', 'dynamic_qr', ['short_code'], unique=True)
            except Exception:
                pass

    # qr_scans table (create if missing)
    if 'qr_scans' not in existing_tables:
        op.create_table(
            'qr_scans',
            sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('qr_id', sa.Integer(), nullable=False),
            sa.Column('scanned_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('ip', sa.String(length=45), nullable=True),
            sa.Column('country', sa.String(length=64), nullable=True),
            sa.Column('region', sa.String(length=64), nullable=True),
            sa.Column('city', sa.String(length=128), nullable=True),
            sa.Column('user_agent', sa.Text(), nullable=True),
            sa.Column('device', sa.String(length=50), nullable=True),
            sa.Column('os', sa.String(length=50), nullable=True),
            sa.Column('browser', sa.String(length=50), nullable=True),
            sa.Column('referrer', sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(['qr_id'], ['dynamic_qr.id'], ondelete='CASCADE'),
        )
        op.create_index('ix_qr_scans_qr_id', 'qr_scans', ['qr_id'])
    else:
        idx_names = {idx['name'] for idx in inspector.get_indexes('qr_scans')}
        if 'ix_qr_scans_qr_id' not in idx_names:
            try:
                op.create_index('ix_qr_scans_qr_id', 'qr_scans', ['qr_id'])
            except Exception:
                pass


def downgrade() -> None:
    # Best effort teardown; ignore if already dropped
    try:
        op.drop_index('ix_qr_scans_qr_id', table_name='qr_scans')
    except Exception:
        pass
    try:
        op.drop_table('qr_scans')
    except Exception:
        pass

    try:
        op.drop_index('ix_dynamic_qr_short_code', table_name='dynamic_qr')
    except Exception:
        pass
    try:
        op.drop_index('ix_dynamic_qr_user_id', table_name='dynamic_qr')
    except Exception:
        pass
    try:
        op.drop_table('dynamic_qr')
    except Exception:
        pass


