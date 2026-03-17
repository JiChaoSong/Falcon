from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session
from app.core.config import settings
# =============================
# Database Configuration
# =============================

# 推荐：后续从 env / config 中读取

# =============================
# Engine
# =============================
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=settings.POOL_PRE_PING,
    pool_size=settings.POOL_SIZE,
    max_overflow=settings.MAX_OVERFLOW,
    echo=settings.DB_ECHO,  # 生产环境关闭
)

# =============================
# Session
# =============================

SessionLocal = scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
)

# =============================
# Base Model
# =============================

Base = declarative_base()

# =============================
# Dependency (FastAPI)
# =============================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =============================
# Init DB
# =============================

def init_db():
    """
    在 main.py / alembic 之前调用
    """
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
