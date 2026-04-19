from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import get_settings


settings = get_settings()
Base = declarative_base()

engine = create_engine(
    settings.sqlalchemy_url,
    future=True,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@contextmanager
def get_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db() -> None:
    with engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {settings.db_schema}"))
    # Import qui per evitare cicli in fase di startup.
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
