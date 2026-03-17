"""convert ids to bigint and disable autoincrement

Revision ID: b8f6d1c0a2f1
Revises: 6941380e7b68
Create Date: 2026-03-17 15:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b8f6d1c0a2f1"
down_revision: Union[str, Sequence[str], None] = "6941380e7b68"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _alter_audit_columns(table_name: str) -> None:
    with op.batch_alter_table(table_name) as batch_op:
        batch_op.alter_column(
            "created_by",
            existing_type=sa.Integer(),
            type_=sa.BigInteger(),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "updated_by",
            existing_type=sa.Integer(),
            type_=sa.BigInteger(),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "deleted_by",
            existing_type=sa.Integer(),
            type_=sa.BigInteger(),
            existing_nullable=True,
        )


def upgrade() -> None:
    tables_with_base_id = [
        "users",
        "projects",
        "project_members",
        "cases",
        "scenarios",
        "scenario_cases",
        "tasks",
        "task_scenarios",
    ]

    for table_name in tables_with_base_id:
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.alter_column(
                "id",
                existing_type=sa.Integer(),
                type_=sa.BigInteger(),
                existing_nullable=False,
                autoincrement=False,
            )
        _alter_audit_columns(table_name)

    with op.batch_alter_table("project_members") as batch_op:
        batch_op.alter_column(
            "project_id",
            existing_type=sa.Integer(),
            type_=sa.BigInteger(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "member_id",
            existing_type=sa.Integer(),
            type_=sa.BigInteger(),
            existing_nullable=False,
        )

    with op.batch_alter_table("cases") as batch_op:
        batch_op.alter_column(
            "project_id",
            existing_type=sa.Integer(),
            type_=sa.BigInteger(),
            existing_nullable=False,
        )

    with op.batch_alter_table("scenarios") as batch_op:
        batch_op.alter_column(
            "project_id",
            existing_type=sa.Integer(),
            type_=sa.BigInteger(),
            existing_nullable=False,
        )

    with op.batch_alter_table("scenario_cases") as batch_op:
        batch_op.alter_column(
            "scenario_id",
            existing_type=sa.Integer(),
            type_=sa.BigInteger(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "case_id",
            existing_type=sa.Integer(),
            type_=sa.BigInteger(),
            existing_nullable=False,
        )

    with op.batch_alter_table("tasks") as batch_op:
        batch_op.alter_column(
            "owner_id",
            existing_type=sa.Integer(),
            type_=sa.BigInteger(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "project_id",
            existing_type=sa.Integer(),
            type_=sa.BigInteger(),
            existing_nullable=False,
        )

    with op.batch_alter_table("task_scenarios") as batch_op:
        batch_op.alter_column(
            "task_id",
            existing_type=sa.Integer(),
            type_=sa.BigInteger(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "scenario_id",
            existing_type=sa.Integer(),
            type_=sa.BigInteger(),
            existing_nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("task_scenarios") as batch_op:
        batch_op.alter_column(
            "scenario_id",
            existing_type=sa.BigInteger(),
            type_=sa.Integer(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "task_id",
            existing_type=sa.BigInteger(),
            type_=sa.Integer(),
            existing_nullable=False,
        )

    with op.batch_alter_table("tasks") as batch_op:
        batch_op.alter_column(
            "project_id",
            existing_type=sa.BigInteger(),
            type_=sa.Integer(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "owner_id",
            existing_type=sa.BigInteger(),
            type_=sa.Integer(),
            existing_nullable=False,
        )

    with op.batch_alter_table("scenario_cases") as batch_op:
        batch_op.alter_column(
            "case_id",
            existing_type=sa.BigInteger(),
            type_=sa.Integer(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "scenario_id",
            existing_type=sa.BigInteger(),
            type_=sa.Integer(),
            existing_nullable=False,
        )

    with op.batch_alter_table("scenarios") as batch_op:
        batch_op.alter_column(
            "project_id",
            existing_type=sa.BigInteger(),
            type_=sa.Integer(),
            existing_nullable=False,
        )

    with op.batch_alter_table("cases") as batch_op:
        batch_op.alter_column(
            "project_id",
            existing_type=sa.BigInteger(),
            type_=sa.Integer(),
            existing_nullable=False,
        )

    with op.batch_alter_table("project_members") as batch_op:
        batch_op.alter_column(
            "member_id",
            existing_type=sa.BigInteger(),
            type_=sa.Integer(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "project_id",
            existing_type=sa.BigInteger(),
            type_=sa.Integer(),
            existing_nullable=False,
        )

    tables_with_base_id = [
        "task_scenarios",
        "tasks",
        "scenario_cases",
        "scenarios",
        "cases",
        "project_members",
        "projects",
        "users",
    ]

    for table_name in tables_with_base_id:
        _downgrade_audit_columns(table_name)
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.alter_column(
                "id",
                existing_type=sa.BigInteger(),
                type_=sa.Integer(),
                existing_nullable=False,
                autoincrement=True,
            )


def _downgrade_audit_columns(table_name: str) -> None:
    with op.batch_alter_table(table_name) as batch_op:
        batch_op.alter_column(
            "deleted_by",
            existing_type=sa.BigInteger(),
            type_=sa.Integer(),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "updated_by",
            existing_type=sa.BigInteger(),
            type_=sa.Integer(),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "created_by",
            existing_type=sa.BigInteger(),
            type_=sa.Integer(),
            existing_nullable=True,
        )
