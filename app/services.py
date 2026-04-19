import json
from datetime import date, timedelta

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, joinedload

from app.auth import hash_password, verify_password
from app.constants import OBJECTIVE_LABEL_BY_SPORT, SPORT_COURSE
from app.models import ExerciseCatalog, User, Workout, WorkoutSchedule, WorkoutSession


def find_user_by_email(session: Session, email: str) -> User | None:
    q = select(User).where(User.email == email.strip().lower())
    return session.scalar(q)


def get_user_by_id(session: Session, user_id: int) -> User | None:
    return session.get(User, user_id)


def create_user(session: Session, full_name: str, email: str, password: str, sex: str) -> User | None:
    normalized_email = email.strip().lower()
    if find_user_by_email(session, normalized_email):
        return None
    normalized_sex = sex if sex in {"male", "female"} else "male"
    user = User(
        full_name=full_name.strip(),
        email=normalized_email,
        password_hash=hash_password(password),
        sex=normalized_sex,
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
        .order_by(desc(Workout.active), Workout.created_at.desc())
    )
    return list(session.scalars(q))


def list_exercise_catalog(session: Session, sport_type: str | None = None) -> list[ExerciseCatalog]:
    q = select(ExerciseCatalog).where(ExerciseCatalog.active.is_(True))
    if sport_type:
        q = q.where(ExerciseCatalog.sport_type == sport_type)
    q = q.order_by(ExerciseCatalog.sport_type.asc(), ExerciseCatalog.name.asc())
    return list(session.scalars(q))


def _normalize_target_area(exercises: list[dict]) -> str:
    zones = []
    for ex in exercises:
        zone = (ex.get("body_zone") or "").strip().lower()
        if zone and zone not in zones and zone != "full_body":
            zones.append(zone)
    if not zones:
        return "Total body"
    return ", ".join(zones[:3])


def _build_exercise_block(sport_type: str, warmup: dict, cooldown: dict, exercises: list[dict]) -> str:
    if sport_type == SPORT_COURSE:
        return "Lezione guidata con istruttore."

    lines = []
    if warmup.get("notes") or warmup.get("minutes"):
        lines.append(f"Riscaldamento: {warmup.get('minutes') or '-'} min - {warmup.get('notes') or ''}".strip())

    objective_label = OBJECTIVE_LABEL_BY_SPORT.get(sport_type, "Obiettivo")
    for idx, ex in enumerate(exercises, start=1):
        mode = ex.get("mode") or "single"
        sets = ex.get("sets") or "-"
        reps = ex.get("reps") or "-"
        duration = ex.get("duration_minutes") or "-"
        objective = ex.get("objective") or "-"
        lines.append(
            f"{idx}. {ex.get('name', 'Esercizio')} [{mode}] sets:{sets} reps:{reps} min:{duration} {objective_label}:{objective}"
        )

    if cooldown.get("notes") or cooldown.get("minutes"):
        lines.append(f"Defaticamento: {cooldown.get('minutes') or '-'} min - {cooldown.get('notes') or ''}".strip())

    return "\n".join(lines) if lines else "Allenamento personalizzato"


def create_workout(
    session: Session,
    user_id: int,
    name: str,
    sport_type: str,
    estimated_minutes: int,
    course_name: str | None,
    warmup: dict,
    cooldown: dict,
    exercises: list[dict],
) -> Workout:
    normalized_sport = sport_type if sport_type in {"swimming", "gym", "running", "course"} else "gym"
    normalized_course = (course_name or "").strip() if normalized_sport == SPORT_COURSE else None
    if normalized_sport == SPORT_COURSE and not normalized_course:
        normalized_course = "corso libero"

    category_map = {
        "swimming": "Nuoto",
        "gym": "Sala pesi",
        "running": "Corsa",
        "course": "Corsi",
    }

    if normalized_sport != SPORT_COURSE:
        normalized_exercises = []
        for ex in exercises:
            catalog_id = ex.get("exercise_catalog_id")
            if not catalog_id:
                continue
            catalog = session.get(ExerciseCatalog, int(catalog_id))
            if not catalog or not catalog.active or catalog.sport_type != normalized_sport:
                continue
            normalized_exercises.append(
                {
                    "exercise_catalog_id": catalog.id,
                    "name": catalog.name,
                    "mode": ex.get("mode") or "single",
                    "sets": ex.get("sets"),
                    "reps": ex.get("reps"),
                    "duration_minutes": ex.get("duration_minutes"),
                    "objective": ex.get("objective"),
                    "body_zone": catalog.body_zone,
                }
            )
        exercises = normalized_exercises

    details = {
        "warmup": warmup,
        "cooldown": cooldown,
        "exercises": exercises,
    }

    workout = Workout(
        user_id=user_id,
        name=name.strip(),
        category=category_map.get(normalized_sport, "Workout"),
        target_area=_normalize_target_area(exercises),
        estimated_minutes=max(1, estimated_minutes),
        exercise_block=_build_exercise_block(normalized_sport, warmup, cooldown, exercises),
        sport_type=normalized_sport,
        course_name=normalized_course,
        detail_json=json.dumps(details, ensure_ascii=True),
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


def list_schedules(session: Session, user_id: int) -> list[WorkoutSchedule]:
    q = (
        select(WorkoutSchedule)
        .options(joinedload(WorkoutSchedule.workout))
        .where(WorkoutSchedule.user_id == user_id)
        .order_by(WorkoutSchedule.start_date.desc())
    )
    return list(session.scalars(q))


def create_schedule(
    session: Session,
    user_id: int,
    workout_id: int,
    start_date: date,
    recurrence_type: str,
    repeat_weeks: int | None,
) -> WorkoutSchedule | None:
    workout = session.scalar(select(Workout).where(Workout.id == workout_id, Workout.user_id == user_id))
    if not workout:
        return None

    normalized_recurrence = recurrence_type if recurrence_type in {"once", "weekly"} else "once"
    weeks = max(1, min(12, repeat_weeks or 1)) if normalized_recurrence == "weekly" else None

    schedule = WorkoutSchedule(
        user_id=user_id,
        workout_id=workout_id,
        start_date=start_date,
        recurrence_type=normalized_recurrence,
        weekday=start_date.weekday() if normalized_recurrence == "weekly" else None,
        repeat_weeks=weeks,
        active=True,
    )
    session.add(schedule)
    session.commit()
    session.refresh(schedule)
    return schedule


def schedule_matches_day(schedule: WorkoutSchedule, day: date) -> bool:
    if not schedule.active:
        return False
    if schedule.recurrence_type == "once":
        return day == schedule.start_date
    if schedule.recurrence_type == "weekly":
        if day < schedule.start_date:
            return False
        if schedule.weekday is None or day.weekday() != schedule.weekday:
            return False
        delta_days = (day - schedule.start_date).days
        week_index = delta_days // 7
        repeat_weeks = schedule.repeat_weeks or 1
        return 0 <= week_index < repeat_weeks
    return False


def list_planned_workouts_for_day(session: Session, user_id: int, day: date) -> list[dict]:
    schedules = list_schedules(session, user_id)
    items = []
    for sched in schedules:
        if sched.workout and schedule_matches_day(sched, day):
            items.append({"schedule": sched, "workout": sched.workout})
    return items


def add_session(
    session: Session,
    user_id: int,
    workout_id: int,
    session_date: date,
    duration_minutes: int | None,
    calories_burned: int | None,
    notes: str | None,
    completed: bool = True,
    schedule_id: int | None = None,
) -> WorkoutSession:
    workout = session.scalar(select(Workout).where(Workout.id == workout_id, Workout.user_id == user_id))
    if not workout:
        raise ValueError("Workout non trovato per questo utente.")

    schedule = None
    if schedule_id:
        schedule = session.scalar(
            select(WorkoutSchedule).where(
                WorkoutSchedule.id == schedule_id,
                WorkoutSchedule.user_id == user_id,
                WorkoutSchedule.workout_id == workout_id,
            )
        )

    item = WorkoutSession(
        user_id=user_id,
        workout_id=workout_id,
        schedule_id=schedule.id if schedule else None,
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


def parse_workout_details(workout: Workout) -> dict:
    if not workout.detail_json:
        return {"warmup": {}, "cooldown": {}, "exercises": []}
    try:
        return json.loads(workout.detail_json)
    except json.JSONDecodeError:
        return {"warmup": {}, "cooldown": {}, "exercises": []}
