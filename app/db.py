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
    with engine.begin() as conn:
        _upgrade_legacy_schema(conn)


def _column_exists(conn, table_name: str, column_name: str) -> bool:
    q = text(
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = :schema
          AND table_name = :table_name
          AND column_name = :column_name
        LIMIT 1
        """
    )
    return bool(
        conn.scalar(
            q,
            {
                "schema": settings.db_schema,
                "table_name": table_name,
                "column_name": column_name,
            },
        )
    )


def _constraint_exists(conn, constraint_name: str) -> bool:
    q = text(
        """
        SELECT 1
        FROM pg_constraint c
        JOIN pg_namespace n ON n.oid = c.connamespace
        WHERE n.nspname = :schema
          AND c.conname = :constraint_name
        LIMIT 1
        """
    )
    return bool(
        conn.scalar(
            q,
            {"schema": settings.db_schema, "constraint_name": constraint_name},
        )
    )


def _ensure_legacy_user(conn) -> int:
    schema = settings.db_schema
    existing = conn.scalar(
        text(
            f"""
            SELECT id
            FROM {schema}.users
            WHERE email = :email
            LIMIT 1
            """
        ),
        {"email": "legacy@myfit.local"},
    )
    if existing:
        return int(existing)

    inserted = conn.scalar(
        text(
            f"""
            INSERT INTO {schema}.users (full_name, email, password_hash, created_at)
            VALUES (:full_name, :email, :password_hash, NOW())
            RETURNING id
            """
        ),
        {
            "full_name": "Legacy User",
            "email": "legacy@myfit.local",
            # Hash non utilizzabile in login: serve solo per ownership dati preesistenti.
            "password_hash": "legacy$disabled",
        },
    )
    return int(inserted)


def _upgrade_legacy_schema(conn) -> None:
    schema = settings.db_schema
    missing_workout_owner = not _column_exists(conn, "workouts", "user_id")
    missing_session_owner = not _column_exists(conn, "workout_sessions", "user_id")
    if not missing_workout_owner and not missing_session_owner:
        return

    legacy_user_id = _ensure_legacy_user(conn)

    if missing_workout_owner:
        conn.execute(text(f"ALTER TABLE {schema}.workouts ADD COLUMN user_id INTEGER"))
        conn.execute(
            text(f"UPDATE {schema}.workouts SET user_id = :legacy_user_id WHERE user_id IS NULL"),
            {"legacy_user_id": legacy_user_id},
        )
        conn.execute(text(f"ALTER TABLE {schema}.workouts ALTER COLUMN user_id SET NOT NULL"))

    if not _constraint_exists(conn, "workouts_user_id_fkey"):
        conn.execute(
            text(
                f"""
                ALTER TABLE {schema}.workouts
                ADD CONSTRAINT workouts_user_id_fkey
                FOREIGN KEY (user_id) REFERENCES {schema}.users(id) ON DELETE CASCADE
                """
            )
        )

    conn.execute(text(f"CREATE INDEX IF NOT EXISTS ix_workouts_user_id ON {schema}.workouts (user_id)"))

    if missing_session_owner:
        conn.execute(text(f"ALTER TABLE {schema}.workout_sessions ADD COLUMN user_id INTEGER"))
        conn.execute(
            text(
                f"""
                UPDATE {schema}.workout_sessions ws
                SET user_id = w.user_id
                FROM {schema}.workouts w
                WHERE ws.workout_id = w.id
                  AND ws.user_id IS NULL
                """
            )
        )
        conn.execute(
            text(
                f"""
                UPDATE {schema}.workout_sessions
                SET user_id = :legacy_user_id
                WHERE user_id IS NULL
                """
            ),
            {"legacy_user_id": legacy_user_id},
        )
        conn.execute(text(f"ALTER TABLE {schema}.workout_sessions ALTER COLUMN user_id SET NOT NULL"))

    if not _constraint_exists(conn, "workout_sessions_user_id_fkey"):
        conn.execute(
            text(
                f"""
                ALTER TABLE {schema}.workout_sessions
                ADD CONSTRAINT workout_sessions_user_id_fkey
                FOREIGN KEY (user_id) REFERENCES {schema}.users(id) ON DELETE CASCADE
                """
            )
        )

    conn.execute(
        text(f"CREATE INDEX IF NOT EXISTS ix_workout_sessions_user_id ON {schema}.workout_sessions (user_id)")
    )
