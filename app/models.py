from datetime import datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import get_settings
from app.db import Base


settings = get_settings()
SCHEMA = settings.db_schema


class Workout(Base):
    __tablename__ = "workouts"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    target_area: Mapped[str] = mapped_column(String(80), nullable=False)
    estimated_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=45)
    exercise_block: Mapped[str] = mapped_column(Text, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    sessions: Mapped[list["WorkoutSession"]] = relationship(
        back_populates="workout",
        cascade="all, delete-orphan",
    )


class WorkoutSession(Base):
    __tablename__ = "workout_sessions"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    workout_id: Mapped[int] = mapped_column(
        ForeignKey(f"{SCHEMA}.workouts.id", ondelete="CASCADE"),
        nullable=False,
    )
    session_date: Mapped[Date] = mapped_column(Date, nullable=False, index=True)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    duration_minutes: Mapped[int | None] = mapped_column(Integer)
    calories_burned: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    workout: Mapped[Workout] = relationship(back_populates="sessions")
