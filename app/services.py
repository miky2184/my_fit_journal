from datetime import date, timedelta

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, joinedload

from app.auth import hash_password, verify_password
from app.models import User, Workout, WorkoutSession


def find_user_by_email(session: Session, email: str) -> User | None:
    q = select(User).where(User.email == email.strip().lower())
    return session.scalar(q)


def get_user_by_id(session: Session, user_id: int) -> User | None:
    return session.get(User, user_id)


def create_user(session: Session, full_name: str, email: str, password: str) -> User | None:
    normalized_email = email.strip().lower()
    if find_user_by_email(session, normalized_email):
        return None
    user = User(
        full_name=full_name.strip(),
        email=normalized_email,
        password_hash=hash_password(password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def authenticate_user(session: Session, email: str, password: str) -> User | None:
    user = find_user_by_email(session, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def list_workouts(session: Session, user_id: int) -> list[Workout]:
    q = (
        select(Workout)
        .where(Workout.user_id == user_id)
        .order_by(desc(Workout.active), Workout.name.asc())
    )
    return list(session.scalars(q))


def create_workout(
    session: Session,
    user_id: int,
    name: str,
    category: str,
    target_area: str,
    estimated_minutes: int,
    exercise_block: str,
) -> Workout:
    workout = Workout(
        user_id=user_id,
        name=name.strip(),
        category=category.strip(),
        target_area=target_area.strip(),
        estimated_minutes=max(1, estimated_minutes),
        exercise_block=exercise_block.strip(),
    )
    session.add(workout)
    session.commit()
    session.refresh(workout)
    return workout


def toggle_workout_active(session: Session, user_id: int, workout_id: int) -> bool:
    workout = session.scalar(select(Workout).where(Workout.id == workout_id, Workout.user_id == user_id))
    if not workout:
        return False
    workout.active = not workout.active
    session.commit()
    return True


def delete_workout(session: Session, user_id: int, workout_id: int) -> bool:
    workout = session.scalar(select(Workout).where(Workout.id == workout_id, Workout.user_id == user_id))
    if not workout:
        return False
    session.delete(workout)
    session.commit()
    return True


def add_session(
    session: Session,
    user_id: int,
    workout_id: int,
    session_date: date,
    duration_minutes: int | None,
    calories_burned: int | None,
    notes: str | None,
    completed: bool = True,
) -> WorkoutSession:
    workout = session.scalar(select(Workout).where(Workout.id == workout_id, Workout.user_id == user_id))
    if not workout:
        raise ValueError("Workout non trovato per questo utente.")

    item = WorkoutSession(
        user_id=user_id,
        workout_id=workout_id,
        session_date=session_date,
        duration_minutes=duration_minutes,
        calories_burned=calories_burned,
        notes=notes.strip() if notes else None,
        completed=completed,
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def list_today_sessions(session: Session, user_id: int, day: date) -> list[WorkoutSession]:
    q = (
        select(WorkoutSession)
        .options(joinedload(WorkoutSession.workout))
        .where(WorkoutSession.user_id == user_id, WorkoutSession.session_date == day)
        .order_by(WorkoutSession.created_at.desc())
    )
    return list(session.scalars(q))


def dashboard_metrics(session: Session, user_id: int) -> dict:
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    total_workouts = session.scalar(
        select(func.count(Workout.id)).where(Workout.user_id == user_id)
    ) or 0

    total_sessions_week = session.scalar(
        select(func.count(WorkoutSession.id)).where(
            WorkoutSession.user_id == user_id,
            WorkoutSession.session_date >= week_start,
        )
    ) or 0

    completed_sessions_week = session.scalar(
        select(func.count(WorkoutSession.id)).where(
            WorkoutSession.user_id == user_id,
            WorkoutSession.session_date >= week_start,
            WorkoutSession.completed.is_(True),
        )
    ) or 0

    month_calories = session.scalar(
        select(func.coalesce(func.sum(WorkoutSession.calories_burned), 0)).where(
            WorkoutSession.user_id == user_id,
            WorkoutSession.session_date >= month_start,
        )
    ) or 0

    top_workouts = session.execute(
        select(Workout.name, func.count(WorkoutSession.id).label("sessions"))
        .join(WorkoutSession, Workout.id == WorkoutSession.workout_id)
        .where(
            WorkoutSession.user_id == user_id,
            WorkoutSession.session_date >= today - timedelta(days=30),
        )
        .group_by(Workout.name)
        .order_by(desc("sessions"))
        .limit(6)
    ).all()

    daily_last_7 = session.execute(
        select(WorkoutSession.session_date, func.count(WorkoutSession.id).label("sessions"))
        .where(
            WorkoutSession.user_id == user_id,
            WorkoutSession.session_date >= today - timedelta(days=6),
        )
        .group_by(WorkoutSession.session_date)
        .order_by(WorkoutSession.session_date.asc())
    ).all()

    count_by_day = {row.session_date.isoformat(): row.sessions for row in daily_last_7}
    daily_series = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        daily_series.append({
            "label": day.strftime("%a"),
            "value": count_by_day.get(day.isoformat(), 0),
        })

    adherence = 0
    if total_sessions_week:
        adherence = round((completed_sessions_week / total_sessions_week) * 100)

    return {
        "total_workouts": total_workouts,
        "total_sessions_week": total_sessions_week,
        "completed_sessions_week": completed_sessions_week,
        "weekly_adherence": adherence,
        "month_calories": month_calories,
        "top_workouts": top_workouts,
        "daily_series": daily_series,
    }
