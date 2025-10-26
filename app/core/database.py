from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
engine_kwargs = {
    "future": True,
    "echo": False,
    "pool_pre_ping": True,
}
connect_args: dict[str, object] = {}

if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    if settings.DATABASE_URL.endswith(":memory:") or settings.DATABASE_URL.startswith("sqlite+pysqlite:///:memory:"):
        engine_kwargs["poolclass"] = StaticPool

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    **engine_kwargs,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    future=True,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that provides a transactional database session."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def run_migrations(revision: str = "head") -> None:
    """Execute Alembic migrations up to the given revision."""
    from alembic import command
    from alembic.config import Config

    project_root = Path(__file__).resolve().parents[2]
    alembic_ini = project_root / "alembic.ini"

    if not alembic_ini.exists():
        msg = "No se encontró archivo alembic.ini en el proyecto"
        raise RuntimeError(msg)

    alembic_cfg = Config(str(alembic_ini))
    alembic_cfg.set_main_option("script_location", str(project_root / "alembic"))
    alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    alembic_cfg.attributes["configure_logger"] = False

    command.upgrade(alembic_cfg, revision)


def init_db() -> None:
    """Apply database migrations when the app starts in non-production environments."""
    run_migrations()
