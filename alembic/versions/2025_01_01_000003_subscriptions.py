"""subscriptions table

Revision ID: subscriptions_0003
Revises: dynamic_qr_scans_0002
Create Date: 2025-01-01 00:20:00

"""
from alembic import op
import sqlalchemy as sa


revision = 'subscriptions_0003'
down_revision = 'dynamic_qr_scans_0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if 'subscriptions' not in existing_tables:
        op.create_table(
            'subscriptions',
            sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('lemon_id', sa.String(length=255), nullable=True),
            sa.Column('status', sa.String(length=50), nullable=False),
            sa.Column('plan', sa.String(length=50), nullable=False),
            sa.Column('renews_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('ends_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        )
        op.create_index('ix_subscriptions_id', 'subscriptions', ['id'])
        op.create_index('ix_subscriptions_user_id', 'subscriptions', ['user_id'])
        op.create_index('ix_subscriptions_status', 'subscriptions', ['status'])
        op.create_index('ix_subscriptions_plan', 'subscriptions', ['plan'])
        op.create_index('ix_subscriptions_lemon_id', 'subscriptions', ['lemon_id'], unique=True)


def downgrade() -> None:
    try:
        op.drop_index('ix_subscriptions_lemon_id', table_name='subscriptions')
    except Exception:
        pass
    try:
        op.drop_index('ix_subscriptions_plan', table_name='subscriptions')
    except Exception:
        pass
    try:
        op.drop_index('ix_subscriptions_status', table_name='subscriptions')
    except Exception:
        pass
    try:
        op.drop_index('ix_subscriptions_user_id', table_name='subscriptions')
    except Exception:
        pass
    try:
        op.drop_index('ix_subscriptions_id', table_name='subscriptions')
    except Exception:
        pass
    try:
        op.drop_table('subscriptions')
    except Exception:
        pass


