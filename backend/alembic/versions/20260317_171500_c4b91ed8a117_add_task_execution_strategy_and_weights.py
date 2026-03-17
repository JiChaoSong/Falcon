"""add task execution strategy and weights

Revision ID: c4b91ed8a117
Revises: 91b1c6a2ee12
Create Date: 2026-03-17 17:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4b91ed8a117"
down_revision: Union[str, Sequence[str], None] = "91b1c6a2ee12"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tasks",
        sa.Column(
            "execution_strategy",
            sa.Enum("SEQUENTIAL", "WEIGHTED", name="task_execution_strategy"),
            nullable=False,
            server_default="SEQUENTIAL",
            comment="执行策略",
        ),
    )
    op.add_column(
        "task_scenarios",
        sa.Column("weight", sa.Integer(), nullable=False, server_default="0", comment="权重"),
    )
    op.add_column(
        "task_scenarios",
        sa.Column("target_users", sa.Integer(), nullable=True, comment="目标用户数"),
    )


def downgrade() -> None:
    op.drop_column("task_scenarios", "target_users")
    op.drop_column("task_scenarios", "weight")
    op.drop_column("tasks", "execution_strategy")
