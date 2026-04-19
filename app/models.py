from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import get_settings
from app.db import Base


settings = get_settings()
SCHEMA = settings.db_schema


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(180), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    sex: Mapped[str] = mapped_column(String(10), nullable=False, default="male")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    workouts: Mapped[list["Workout"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    sessions: Mapped[list["WorkoutSession"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    schedules: Mapped[list["WorkoutSchedule"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Workout(Base):
    __tablename__ = "workouts"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey(f"{SCHEMA}.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    target_area: Mapped[str] = mapped_column(String(80), nullable=False)
    estimated_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=45)
    exercise_block: Mapped[str] = mapped_column(Text, nullable=False)
    sport_type: Mapped[str] = mapped_column(String(30), nullable=False, default="gym")
    course_name: Mapped[str | None] = mapped_column(String(120))
    detail_json: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    sessions: Mapped[list["WorkoutSession"]] = relationship(
        back_populates="workout",
        cascade="all, delete-orphan",
    )
    schedules: Mapped[list["WorkoutSchedule"]] = relationship(
        back_populates="workout",
        cascade="all, delete-orphan",
    )
    user: Mapped[User] = relationship(back_populates="workouts")


class WorkoutSchedule(Base):
    __tablename__ = "workout_schedules"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey(f"{SCHEMA}.users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workout_id: Mapped[int] = mapped_column(
        ForeignKey(f"{SCHEMA}.workouts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    recurrence_type: Mapped[str] = mapped_column(String(20), nullable=False, default="once")
    weekday: Mapped[int | None] = mapped_column(Integer)
    repeat_weeks: Mapped[int | None] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    user: Mapped[User] = relationship(back_populates="schedules")
    workout: Mapped[Workout] = relationship(back_populates="schedules")
    sessions: Mapped[list["WorkoutSession"]] = relationship(back_populates="schedule")


class WorkoutSession(Base):
    __tablename__ = "workout_sessions"
    __table_args__ = {"schema": SCHEMA}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey(f"{SCHEMA}.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workout_id: Mapped[int] = mapped_column(
        ForeignKey(f"{SCHEMA}.workouts.id", ondelete="CASCADE"),
        nullable=False,
    )
    schedule_id: Mapped[int | None] = mapped_column(
        ForeignKey(f"{SCHEMA}.workout_schedules.id", ondelete="SET NULL")
    )
    session_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    duration_minutes: Mapped[int | None] = mapped_column(Integer)
    calories_burned: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    workout: Mapped[Workout] = relationship(back_populates="sessions")
    user: Mapped[User] = relationship(back_populates="sessions")
    schedule: Mapped[WorkoutSchedule | None] = relationship(back_populates="sessions")
