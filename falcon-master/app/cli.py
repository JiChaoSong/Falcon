#!/user/bin/env python3
# -*- coding: utf-8 -*-
"""
--------------------------------------
    Author:     JiChao_Song
    Date  :     2026-02-02 21:34 
    Name  :     cli.py
    Desc  :     
--------------------------------------
"""
import sys
import subprocess
from pathlib import Path

# 将项目根目录添加到sys.path的最前面
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import typer
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.security import get_password_hash
from app.db import get_db
from app.models.users import Users

app_command = typer.Typer()
db_command = typer.Typer(help="数据库迁移相关命令")
app_command.add_typer(db_command, name="db")


def _run_alembic(*args: str) -> None:
    """统一执行 Alembic 命令，避免每次手写原始命令。"""
    command = [
        sys.executable,
        "-m",
        "alembic",
        "-c",
        str(project_root / "alembic.ini"),
        *args,
    ]

    try:
        subprocess.run(command, cwd=project_root, check=True)
    except subprocess.CalledProcessError as exc:
        typer.echo(f"❌ Alembic 执行失败，退出码: {exc.returncode}", err=True)
        raise typer.Exit(code=exc.returncode)


@app_command.command()
def create_admin(
    name: str = typer.Option(..., prompt=True),
    username: str = typer.Option(..., prompt=True),
    password: str = typer.Option(..., prompt=True)
):
    """创建管理员用户"""
    db = next(get_db())
    try:
        # 检查用户是否已存在
        existing_user = db.execute(
            select(Users).where(
                (Users.username == username)
            )
        ).scalar_one_or_none()

        if existing_user:
            typer.echo(f"❌ 用户 {username}  已存在！", err=True)
            sys.exit(1)
        admin = Users(
            username=username,
            name=name,
            is_admin=True,
        )

        admin.set_password(password)

        # ... 创建逻辑
        db.add(admin)
        db.commit()
        db.refresh(admin)
        typer.echo(f"✅ 管理员 {username} 创建成功！")
    except IntegrityError as e:
        db.rollback()
        typer.echo(f"❌ 数据库错误: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        db.rollback()
        typer.echo(f"❌ 未知错误: {e}", err=True)
        sys.exit(1)
    finally:
        db.close()

@app_command.command()
def check_db():
    """检查数据库连接"""
    try:
        db = next(get_db())
        # 执行简单查询测试连接
        result = db.execute("SELECT 1").scalar()
        if result == 1:
            typer.echo("✅ 数据库连接正常！")
        db.close()
    except Exception as e:
        typer.echo(f"❌ 数据库连接失败: {e}", err=True)
        sys.exit(1)


@db_command.command("upgrade")
def db_upgrade(revision: str = typer.Argument("head", help="升级目标版本，默认 head")):
    """执行数据库升级。"""
    _run_alembic("upgrade", revision)


@db_command.command("downgrade")
def db_downgrade(revision: str = typer.Argument("-1", help="回退目标版本，默认 -1")):
    """执行数据库回退。"""
    _run_alembic("downgrade", revision)


@db_command.command("revision")
def db_revision(
    message: str = typer.Option(..., "--message", "-m", help="迁移说明"),
    autogenerate: bool = typer.Option(True, help="是否自动生成迁移内容"),
):
    """创建新的迁移脚本。"""
    command = ["revision"]
    if autogenerate:
        command.append("--autogenerate")
    command.extend(["-m", message])
    _run_alembic(*command)


@db_command.command("current")
def db_current():
    """查看当前数据库版本。"""
    _run_alembic("current")


@db_command.command("history")
def db_history():
    """查看迁移历史。"""
    _run_alembic("history")


@db_command.command("stamp")
def db_stamp(revision: str = typer.Argument("head", help="标记到指定版本，默认 head")):
    """直接标记数据库版本，不执行迁移。"""
    _run_alembic("stamp", revision)


if __name__ == '__main__':
    app_command()
