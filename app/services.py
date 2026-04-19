import json
from datetime import date, timedelta
import calendar

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, joinedload

from app.auth import hash_password, verify_password
from app.constants import SPORT_COURSE
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


def _build_phase_summary(sport_type: str, phases: list[dict]) -> str:
    if sport_type == SPORT_COURSE:
        return "Lezione guidata con istruttore."

    lines = []
    for idx, phase in enumerate(phases, start=1):
        phase_type = phase.get("phase_type") or "fase"
        duration_type = phase.get("duration_type")
        duration_value = phase.get("duration_value")
        repeats = phase.get("repeat_count") or 1
        exercise_name = phase.get("exercise_name")
        intensity = phase.get("intensity_value")
        style = phase.get("swim_style")
        equipment = phase.get("equipment")
        reps = phase.get("reps")
        weight = phase.get("weight_kg")

        details = []
        if duration_value and duration_type:
            details.append(f"durata {duration_value} ({duration_type})")
        if exercise_name:
            details.append(f"esercizio {exercise_name}")
        if intensity:
            details.append(f"intensita {intensity}")
        if style:
            details.append(f"stile {style}")
        if equipment:
            details.append(f"attrezzatura {equipment}")
        if reps:
            details.append(f"reps {reps}")
        if weight:
            details.append(f"kg {weight}")
        if repeats and repeats > 1:
            details.append(f"x{repeats}")

        lines.append(f"{idx}. {phase_type}: " + (" - ".join(details) if details else "configurata"))

    return "\n".join(lines) if lines else "Allenamento a fasi"


def _normalize_phases(session: Session, sport_type: str, phases: list[dict]) -> list[dict]:
    cleaned = []
    for phase in phases:
        phase_type = (phase.get("phase_type") or "").strip().lower()
        duration_type = (phase.get("duration_type") or "").strip().lower()
        duration_value = phase.get("duration_value")
        repeat_count = phase.get("repeat_count") or 1
        if not phase_type:
            continue

        if sport_type in {"running", "swimming"} and not duration_value:
            continue

        item = {
            "phase_type": phase_type,
            "duration_type": None,
            "duration_value": None,
            "repeat_count": max(1, int(repeat_count)),
        }

        if sport_type == "running":
            allowed_units = {"time", "meters", "kilometers"}
            item["duration_type"] = duration_type if duration_type in allowed_units else "time"
            item["duration_value"] = str(duration_value).strip()
        elif sport_type == "swimming":
            allowed_units = {"time", "meters"}
            item["duration_type"] = duration_type if duration_type in allowed_units else "time"
            item["duration_value"] = str(duration_value).strip()

        if sport_type == "running":
            item["intensity_mode"] = (phase.get("intensity_mode") or "pace").strip().lower()
            item["intensity_value"] = (phase.get("intensity_value") or "").strip() or None
            item["body_zone"] = "full_body"

        if sport_type == "swimming":
            item["swim_style"] = (phase.get("swim_style") or "stile libero").strip().lower()
            item["equipment"] = (phase.get("equipment") or "nessuno").strip().lower()
            item["body_zone"] = "full_body"

        if sport_type == "gym":
            catalog_id = phase.get("exercise_catalog_id")
            if not catalog_id:
                continue
            try:
                catalog = session.get(ExerciseCatalog, int(catalog_id))
            except (TypeError, ValueError):
                continue
            if not catalog or not catalog.active or catalog.sport_type != "gym":
                continue
            item["exercise_catalog_id"] = catalog.id
            item["exercise_name"] = catalog.name
            item["body_zone"] = catalog.body_zone
            item["reps"] = int(phase.get("reps") or 0) or None
            item["weight_kg"] = float(phase.get("weight_kg") or 0) or None

        cleaned.append(item)
    return cleaned


def create_workout(
    session: Session,
    user_id: int,
    name: str,
    sport_type: str,
    estimated_minutes: int,
    course_name: str | None,
    phases: list[dict],
) -> Workout:
    normalized_sport = sport_type if sport_type in {"swimming", "gym", "running", "course"} else "gym"
    normalized_course = (course_name or "").strip() if normalized_sport == SPORT_COURSE else None
    if normalized_sport == SPORT_COURSE and not normalized_course:
        normalized_course = "corso libero"
    resolved_name = name.strip()
    if normalized_sport == SPORT_COURSE and normalized_course:
        resolved_name = normalized_course
    if not resolved_name:
        resolved_name = normalized_course or "workout senza nome"

    category_map = {
        "swimming": "Nuoto",
        "gym": "Sala pesi",
        "running": "Corsa",
        "course": "Corsi",
    }

    normalized_phases = _normalize_phases(session, normalized_sport, phases)
    details = {"phases": normalized_phases}

    workout = Workout(
        user_id=user_id,
        name=resolved_name,
        category=category_map.get(normalized_sport, "Workout"),
        target_area=_normalize_target_area(normalized_phases),
        estimated_minutes=max(1, estimated_minutes),
        exercise_block=_build_phase_summary(normalized_sport, normalized_phases),
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
    recurrence_days: list[int] | None,
    end_after_weeks: int | None,
    end_date: date | None,
) -> WorkoutSchedule | None:
    workout = session.scalar(select(Workout).where(Workout.id == workout_id, Workout.user_id == user_id))
    if not workout:
        return None

    normalized_recurrence = recurrence_type if recurrence_type in {"once", "weekly"} else "once"
    days = sorted({d for d in (recurrence_days or []) if 0 <= d <= 6})
    if normalized_recurrence == "weekly" and not days:
        days = [start_date.weekday()]

    weeks = max(1, min(52, end_after_weeks or 1)) if normalized_recurrence == "weekly" and end_after_weeks else None

    schedule = WorkoutSchedule(
        user_id=user_id,
        workout_id=workout_id,
        start_date=start_date,
        recurrence_type=normalized_recurrence,
        weekday=start_date.weekday() if normalized_recurrence == "weekly" else None,
        repeat_weeks=weeks,
        recurrence_days=",".join(str(d) for d in days) if normalized_recurrence == "weekly" else None,
        end_after_weeks=weeks,
        end_date=end_date if normalized_recurrence == "weekly" else None,
        excluded_dates_json="[]",
        active=True,
    )
    session.add(schedule)
    session.commit()
    session.refresh(schedule)
    return schedule


def _schedule_days(schedule: WorkoutSchedule) -> set[int]:
    if schedule.recurrence_days:
        try:
            return {int(x) for x in schedule.recurrence_days.split(",") if x.strip() != ""}
        except ValueError:
            pass
    if schedule.weekday is not None:
        return {schedule.weekday}
    return {schedule.start_date.weekday()}


def _schedule_excluded_dates(schedule: WorkoutSchedule) -> set[date]:
    if not schedule.excluded_dates_json:
        return set()
    try:
        payload = json.loads(schedule.excluded_dates_json)
    except json.JSONDecodeError:
        return set()
    if not isinstance(payload, list):
        return set()
    out = set()
    for item in payload:
        try:
            out.add(date.fromisoformat(str(item)))
        except ValueError:
            continue
    return out


def schedule_matches_day(schedule: WorkoutSchedule, day: date) -> bool:
    if not schedule.active:
        return False
    if day in _schedule_excluded_dates(schedule):
        return False
    if schedule.recurrence_type == "once":
        return day == schedule.start_date
    if schedule.recurrence_type == "weekly":
        if day < schedule.start_date:
            return False
        if schedule.end_date and day > schedule.end_date:
            return False
        if day.weekday() not in _schedule_days(schedule):
            return False
        delta_days = (day - schedule.start_date).days
        week_index = delta_days // 7
        repeat_weeks = schedule.end_after_weeks or schedule.repeat_weeks
        if repeat_weeks:
            return 0 <= week_index < repeat_weeks
        return week_index >= 0
    return False


def list_planned_workouts_for_day(session: Session, user_id: int, day: date) -> list[dict]:
    schedules = list_schedules(session, user_id)
    items = []
    for sched in schedules:
        if sched.workout and schedule_matches_day(sched, day):
            items.append({"schedule": sched, "workout": sched.workout})
    return items


def list_calendar_occurrences_for_month(session: Session, user_id: int, month: date) -> dict[str, list[dict]]:
    schedules = list_schedules(session, user_id)
    _, last_day = calendar.monthrange(month.year, month.month)
    start = date(month.year, month.month, 1)
    end = date(month.year, month.month, last_day)

    by_day: dict[str, list[dict]] = {}
    current = start
    while current <= end:
        key = current.isoformat()
        by_day[key] = []
        for sched in schedules:
            if sched.workout and schedule_matches_day(sched, current):
                by_day[key].append({"schedule": sched, "workout": sched.workout})
        current += timedelta(days=1)
    return by_day


def remove_schedule_occurrence(
    session: Session,
    user_id: int,
    schedule_id: int,
    occurrence_date: date,
    scope: str,
) -> bool:
    schedule = session.scalar(
        select(WorkoutSchedule).where(
            WorkoutSchedule.id == schedule_id,
            WorkoutSchedule.user_id == user_id,
        )
    )
    if not schedule:
        return False

    normalized_scope = scope if scope in {"single", "series"} else "single"
    if normalized_scope == "series" or schedule.recurrence_type == "once":
        session.delete(schedule)
        session.commit()
        return True

    excluded = _schedule_excluded_dates(schedule)
    excluded.add(occurrence_date)
    schedule.excluded_dates_json = json.dumps(sorted(d.isoformat() for d in excluded), ensure_ascii=True)
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
