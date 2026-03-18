from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

# =============================
# Database Configuration
# =============================

database_url = make_url(settings.DATABASE_URL)
connect_args: dict[str, str] = {}

if database_url.get_backend_name().startswith("mysql"):
    # Keep every DB session in UTC so server-side NOW()/CURRENT_TIMESTAMP
    # and application-side aware datetimes represent the same instant.
    connect_args["init_command"] = "SET time_zone = '+00:00'"

# =============================
# Engine
# =============================
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=settings.POOL_PRE_PING,
    pool_size=settings.POOL_SIZE,
    max_overflow=settings.MAX_OVERFLOW,
    pool_recycle=settings.POOL_RECYCLE,
    pool_timeout=settings.POOL_TIMEOUT,
    pool_reset_on_return="rollback",
    connect_args=connect_args,
    echo=settings.DB_ECHO,
)

# =============================
# Session
# =============================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# =============================
# Base Model
# =============================

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
