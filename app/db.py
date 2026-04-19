from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import get_settings
from app.constants import EXERCISE_CATALOG_SEED


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
        _seed_exercise_catalog(conn)


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
            INSERT INTO {schema}.users (full_name, email, password_hash, sex, created_at)
            VALUES (:full_name, :email, :password_hash, :sex, NOW())
            RETURNING id
            """
        ),
        {
            "full_name": "Legacy User",
            "email": "legacy@myfit.local",
            # Hash non utilizzabile in login: serve solo per ownership dati preesistenti.
            "password_hash": "legacy$disabled",
            "sex": "male",
        },
    )
    return int(inserted)


def _upgrade_legacy_schema(conn) -> None:
    schema = settings.db_schema
    missing_workout_owner = not _column_exists(conn, "workouts", "user_id")
    missing_session_owner = not _column_exists(conn, "workout_sessions", "user_id")
    has_legacy_ownership_gap = missing_workout_owner or missing_session_owner

    if has_legacy_ownership_gap:
        legacy_user_id = _ensure_legacy_user(conn)
    else:
        legacy_user_id = None

    if missing_workout_owner and legacy_user_id is not None:
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

    if missing_session_owner and legacy_user_id is not None:
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

    conn.execute(text(f"CREATE INDEX IF NOT EXISTS ix_workout_sessions_user_id ON {schema}.workout_sessions (user_id)"))

    if not _column_exists(conn, "users", "sex"):
        conn.execute(text(f"ALTER TABLE {schema}.users ADD COLUMN sex VARCHAR(10)"))
        conn.execute(text(f"UPDATE {schema}.users SET sex = 'male' WHERE sex IS NULL"))
        conn.execute(text(f"ALTER TABLE {schema}.users ALTER COLUMN sex SET NOT NULL"))
        conn.execute(text(f"ALTER TABLE {schema}.users ALTER COLUMN sex SET DEFAULT 'male'"))

    if not _column_exists(conn, "workouts", "sport_type"):
        conn.execute(text(f"ALTER TABLE {schema}.workouts ADD COLUMN sport_type VARCHAR(30)"))
        conn.execute(text(f"UPDATE {schema}.workouts SET sport_type = 'gym' WHERE sport_type IS NULL"))
        conn.execute(text(f"ALTER TABLE {schema}.workouts ALTER COLUMN sport_type SET NOT NULL"))
        conn.execute(text(f"ALTER TABLE {schema}.workouts ALTER COLUMN sport_type SET DEFAULT 'gym'"))

    if not _column_exists(conn, "workouts", "course_name"):
        conn.execute(text(f"ALTER TABLE {schema}.workouts ADD COLUMN course_name VARCHAR(120)"))

    if not _column_exists(conn, "workouts", "detail_json"):
        conn.execute(text(f"ALTER TABLE {schema}.workouts ADD COLUMN detail_json TEXT"))

    if not _column_exists(conn, "workout_sessions", "schedule_id"):
        conn.execute(text(f"ALTER TABLE {schema}.workout_sessions ADD COLUMN schedule_id INTEGER"))

    if not _constraint_exists(conn, "workout_sessions_schedule_id_fkey"):
        conn.execute(
            text(
                f"""
                ALTER TABLE {schema}.workout_sessions
                ADD CONSTRAINT workout_sessions_schedule_id_fkey
                FOREIGN KEY (schedule_id) REFERENCES {schema}.workout_schedules(id) ON DELETE SET NULL
                """
            )
        )


def _seed_exercise_catalog(conn) -> None:
    schema = settings.db_schema
    for row in EXERCISE_CATALOG_SEED:
        conn.execute(
            text(
                f"""
                INSERT INTO {schema}.exercise_catalog (sport_type, name, body_zone, active, created_at)
                VALUES (:sport_type, :name, :body_zone, TRUE, NOW())
                ON CONFLICT (sport_type, name) DO NOTHING
                """
            ),
            {
                "sport_type": row["sport_type"],
                "name": row["name"],
                "body_zone": row["body_zone"],
            },
        )
