"""add workers table

Revision ID: a7f4b1c2d3e4
Revises: f3d02931aba7
Create Date: 2026-03-18 15:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a7f4b1c2d3e4"
down_revision: Union[str, Sequence[str], None] = "f3d02931aba7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "workers",
        sa.Column("worker_id", sa.String(length=100), nullable=False),
        sa.Column("host", sa.String(length=100), nullable=False),
        sa.Column("port", sa.Integer(), nullable=False),
        sa.Column("address", sa.String(length=200), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=True),
        sa.Column(
            "status",
            sa.Enum("ONLINE", "BUSY", "DEGRADED", "OFFLINE", "DISABLED", name="worker_status"),
            nullable=False,
            server_default="ONLINE",
        ),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("running_tasks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("scheduling_weight", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_heartbeat_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_error", sa.String(length=500), nullable=True),
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("created_by_name", sa.String(length=50), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_by_name", sa.String(length=50), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.BigInteger(), nullable=True),
        sa.Column("deleted_by_name", sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_workers_id"), "workers", ["id"], unique=False)
    op.create_index(op.f("ix_workers_worker_id"), "workers", ["worker_id"], unique=True)
    op.create_index(op.f("ix_workers_address"), "workers", ["address"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_workers_address"), table_name="workers")
    op.drop_index(op.f("ix_workers_worker_id"), table_name="workers")
    op.drop_index(op.f("ix_workers_id"), table_name="workers")
    op.drop_table("workers")
    sa.Enum(name="worker_status").drop(op.get_bind(), checkfirst=True)
