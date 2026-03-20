"""add task completion policy

Revision ID: e1a4c6b7d8f9
Revises: 5f2c1d9e8a77
Create Date: 2026-03-20 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e1a4c6b7d8f9"
down_revision: Union[str, Sequence[str], None] = "5f2c1d9e8a77"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tasks",
        sa.Column(
            "completion_policy",
            sa.Enum("GRACEFUL", "FORCE", name="task_completion_policy"),
            nullable=False,
            server_default="GRACEFUL",
            comment="结束策略",
        ),
    )


def downgrade() -> None:
    op.drop_column("tasks", "completion_policy")
