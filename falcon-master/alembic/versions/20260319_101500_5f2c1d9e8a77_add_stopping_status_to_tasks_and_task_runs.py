"""add stopping status to tasks and task runs

Revision ID: 5f2c1d9e8a77
Revises: a7f4b1c2d3e4
Create Date: 2026-03-19 10:15:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "5f2c1d9e8a77"
down_revision: Union[str, Sequence[str], None] = "a7f4b1c2d3e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE tasks
        MODIFY COLUMN status ENUM('PENDING', 'RUNNING', 'STOPPING', 'COMPLETED', 'FAILED', 'CANCELED')
        NOT NULL
        """
    )
    op.execute(
        """
        ALTER TABLE task_runs
        MODIFY COLUMN status ENUM('PENDING', 'RUNNING', 'STOPPING', 'COMPLETED', 'FAILED', 'CANCELED')
        NOT NULL
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE task_runs
        MODIFY COLUMN status ENUM('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELED')
        NOT NULL
        """
    )
    op.execute(
        """
        ALTER TABLE tasks
        MODIFY COLUMN status ENUM('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELED')
        NOT NULL
        """
    )
