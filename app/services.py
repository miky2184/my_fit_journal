from datetime import date, timedelta

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, joinedload

from app.models import Workout, WorkoutSession


def list_workouts(session: Session) -> list[Workout]:
    q = select(Workout).order_by(desc(Workout.active), Workout.name.asc())
    return list(session.scalars(q))


def create_workout(
    session: Session,
    name: str,
    category: str,
    target_area: str,
    estimated_minutes: int,
    exercise_block: str,
) -> Workout:
    workout = Workout(
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


def toggle_workout_active(session: Session, workout_id: int) -> bool:
    workout = session.get(Workout, workout_id)
    if not workout:
        return False
    workout.active = not workout.active
    session.commit()
    return True


def delete_workout(session: Session, workout_id: int) -> bool:
    workout = session.get(Workout, workout_id)
    if not workout:
        return False
    session.delete(workout)
    session.commit()
    return True


def add_session(
    session: Session,
    workout_id: int,
    session_date: date,
    duration_minutes: int | None,
    calories_burned: int | None,
    notes: str | None,
    completed: bool = True,
) -> WorkoutSession:
    item = WorkoutSession(
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


def list_today_sessions(session: Session, day: date) -> list[WorkoutSession]:
    q = (
        select(WorkoutSession)
        .options(joinedload(WorkoutSession.workout))
        .where(WorkoutSession.session_date == day)
        .order_by(WorkoutSession.created_at.desc())
    )
    return list(session.scalars(q))


def dashboard_metrics(session: Session) -> dict:
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    total_workouts = session.scalar(select(func.count(Workout.id))) or 0

    total_sessions_week = session.scalar(
        select(func.count(WorkoutSession.id)).where(WorkoutSession.session_date >= week_start)
    ) or 0

    completed_sessions_week = session.scalar(
        select(func.count(WorkoutSession.id)).where(
            WorkoutSession.session_date >= week_start,
            WorkoutSession.completed.is_(True),
        )
    ) or 0

    month_calories = session.scalar(
        select(func.coalesce(func.sum(WorkoutSession.calories_burned), 0)).where(
            WorkoutSession.session_date >= month_start,
        )
    ) or 0

    top_workouts = session.execute(
        select(Workout.name, func.count(WorkoutSession.id).label("sessions"))
        .join(WorkoutSession, Workout.id == WorkoutSession.workout_id)
        .where(WorkoutSession.session_date >= today - timedelta(days=30))
        .group_by(Workout.name)
        .order_by(desc("sessions"))
        .limit(6)
    ).all()

    daily_last_7 = session.execute(
        select(WorkoutSession.session_date, func.count(WorkoutSession.id).label("sessions"))
        .where(WorkoutSession.session_date >= today - timedelta(days=6))
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
