from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # SQLite requires this for multi-threaded use
)


@event.listens_for(engine, "connect")
def _enable_sqlite_fk(dbapi_connection, connection_record) -> None:  # type: ignore[no-untyped-def]
    """Enable ON DELETE CASCADE enforcement in SQLite (off by default)."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a DB session and closes it on exit."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all_tables() -> None:
    """Create all tables defined in SQLAlchemy models. Called at startup."""
    Base.metadata.create_all(bind=engine)


def apply_column_migrations() -> None:
    """Add columns that postdate an existing database's initial creation.

    SQLAlchemy create_all does not ALTER existing tables, so new columns must
    be applied here. Each block is idempotent: it inspects the live schema
    before issuing ALTER TABLE, so re-running on an up-to-date database is safe.
    """
    from sqlalchemy import inspect, text  # local import avoids module-load cost

    inspector = inspect(engine)
    existing_message_cols = {c["name"] for c in inspector.get_columns("messages")}

    # messages.is_fallback — added in T057a
    if "is_fallback" not in existing_message_cols:
        with engine.begin() as conn:
            conn.execute(
                text("ALTER TABLE messages ADD COLUMN is_fallback BOOLEAN NOT NULL DEFAULT 0")
            )
