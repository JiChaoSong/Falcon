"""add task runs and metrics

Revision ID: 91b1c6a2ee12
Revises: b8f6d1c0a2f1
Create Date: 2026-03-17 16:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "91b1c6a2ee12"
down_revision: Union[str, Sequence[str], None] = "b8f6d1c0a2f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "task_runs",
        sa.Column("task_id", sa.BigInteger(), nullable=False, comment="任务id"),
        sa.Column(
            "status",
            sa.Enum("PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELED", name="task_run_status"),
            nullable=False,
            comment="运行状态",
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True, comment="开始时间"),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True, comment="结束时间"),
        sa.Column("runtime_seconds", sa.Integer(), nullable=False, comment="运行时长（秒）"),
        sa.Column("summary_json", sa.JSON(), nullable=True, comment="汇总数据"),
        sa.Column("error_message", sa.String(length=500), nullable=True, comment="错误信息"),
        sa.Column("id", sa.BigInteger(), nullable=False, comment="主键ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="创建人ID"),
        sa.Column("created_by_name", sa.String(length=50), nullable=True, comment="创建人"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="更新时间"),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="更新人ID"),
        sa.Column("updated_by_name", sa.String(length=50), nullable=True, comment="更新人"),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, comment="是否已删除"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True, comment="删除时间"),
        sa.Column("deleted_by", sa.BigInteger(), nullable=True, comment="删除人ID"),
        sa.Column("deleted_by_name", sa.String(length=50), nullable=True, comment="删除人"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_task_runs_id"), "task_runs", ["id"], unique=False)

    op.create_table(
        "task_metrics_second",
        sa.Column("task_run_id", sa.BigInteger(), nullable=False, comment="任务运行id"),
        sa.Column("task_id", sa.BigInteger(), nullable=False, comment="任务id"),
        sa.Column("scenario_id", sa.BigInteger(), nullable=True, comment="场景id"),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False, comment="指标窗口时间"),
        sa.Column("rps", sa.Float(), nullable=False, comment="每秒请求数"),
        sa.Column("success_count", sa.Integer(), nullable=False, comment="成功数"),
        sa.Column("fail_count", sa.Integer(), nullable=False, comment="失败数"),
        sa.Column("avg_rt", sa.Float(), nullable=False, comment="平均响应时间ms"),
        sa.Column("p95", sa.Float(), nullable=False, comment="P95响应时间ms"),
        sa.Column("p99", sa.Float(), nullable=False, comment="P99响应时间ms"),
        sa.Column("active_users", sa.Integer(), nullable=False, comment="活跃用户数"),
        sa.Column("id", sa.BigInteger(), nullable=False, comment="主键ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="创建时间"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="创建人ID"),
        sa.Column("created_by_name", sa.String(length=50), nullable=True, comment="创建人"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False, comment="更新时间"),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="更新人ID"),
        sa.Column("updated_by_name", sa.String(length=50), nullable=True, comment="更新人"),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, comment="是否已删除"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True, comment="删除时间"),
        sa.Column("deleted_by", sa.BigInteger(), nullable=True, comment="删除人ID"),
        sa.Column("deleted_by_name", sa.String(length=50), nullable=True, comment="删除人"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_task_metrics_second_id"), "task_metrics_second", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_task_metrics_second_id"), table_name="task_metrics_second")
    op.drop_table("task_metrics_second")
    op.drop_index(op.f("ix_task_runs_id"), table_name="task_runs")
    op.drop_table("task_runs")
