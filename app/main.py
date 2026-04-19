import calendar
import json
from datetime import date, timedelta
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

from app.auth import build_session_cookie_flags
from app.calendar_it import italy_holidays
from app.config import get_settings
from app.constants import COURSE_OPTIONS, SPORT_OPTIONS
from app.db import get_session, init_db
from app.services import (
    add_session,
    authenticate_user,
    create_schedule,
    create_user,
    create_workout,
    dashboard_metrics,
    delete_workout,
    get_user_by_id,
    list_calendar_occurrences_for_month,
    list_exercise_catalog,
    list_planned_workouts_for_day,
    list_today_sessions,
    list_workouts,
    parse_workout_details,
    remove_schedule_occurrence,
    toggle_workout_active,
)


app = FastAPI(title="MyFit Journal")
settings = get_settings()

cookie_flags = build_session_cookie_flags(
    settings.app_env,
    settings.session_https_only,
)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    https_only=bool(cookie_flags["https_only"]),
    same_site=str(cookie_flags["same_site"]),
    session_cookie="myfit_session",
)

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


class LoginPayload(BaseModel):
    email: str
    password: str


@app.on_event("startup")
def on_startup() -> None:
    init_db()


def require_user_id(request: Request) -> int | None:
    user_id = request.session.get("user_id")
    if isinstance(user_id, int):
        return user_id
    return None


def current_user(request: Request) -> dict | None:
    user_id = require_user_id(request)
    if not user_id:
        return None

    with get_session() as session:
        user = get_user_by_id(session, user_id)
    if not user:
        request.session.clear()
        return None
    return {"id": user.id, "full_name": user.full_name, "email": user.email, "sex": user.sex}


def render(request: Request, template: str, context: dict):
    payload = dict(context)
    payload["request"] = request
    payload["current_user"] = current_user(request)
    return templates.TemplateResponse(template, payload)


def _parse_phases_json(raw: str | None) -> list[dict]:
    if not raw:
        return []
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return []

    if not isinstance(payload, list):
        return []

    cleaned = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        cleaned.append(
            {
                "exercise_catalog_id": int(item.get("exercise_catalog_id") or 0) or None,
                "phase_type": str(item.get("phase_type", "")).strip().lower(),
                "duration_type": str(item.get("duration_type", "")).strip().lower() or None,
                "duration_value": str(item.get("duration_value", "")).strip() or None,
                "repeat_count": int(item.get("repeat_count") or 1),
                "reps": int(item.get("reps") or 0) or None,
                "weight_kg": float(item.get("weight_kg") or 0) or None,
                "intensity_mode": str(item.get("intensity_mode", "")).strip().lower() or None,
                "intensity_value": str(item.get("intensity_value", "")).strip() or None,
                "swim_style": str(item.get("swim_style", "")).strip().lower() or None,
                "equipment": str(item.get("equipment", "")).strip().lower() or None,
                "body_zone": str(item.get("body_zone", "full_body")).strip() or "full_body",
            }
        )
    return cleaned


def _month_start(month_str: str | None) -> date:
    if month_str:
        try:
            return date.fromisoformat(f"{month_str}-01")
        except ValueError:
            pass
    return date.today().replace(day=1)


@app.get("/")
def home(request: Request):
    if not require_user_id(request):
        return RedirectResponse(url="/login", status_code=302)

    user_agent = (request.headers.get("user-agent") or "").lower()
    if "iphone" in user_agent or "android" in user_agent:
        return RedirectResponse(url="/today", status_code=302)
    return RedirectResponse(url="/dashboard", status_code=302)


@app.get("/register")
def register_page(request: Request):
    if require_user_id(request):
        return RedirectResponse(url="/dashboard", status_code=302)
    return render(request, "register.html", {"page": "auth", "error": None})


@app.post("/register")
def register_action(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    sex: str = Form("male"),
):
    if len(password) < 8:
        return render(
            request,
            "register.html",
            {
                "page": "auth",
                "error": "La password deve contenere almeno 8 caratteri.",
            },
        )

    with get_session() as session:
        user = create_user(session, full_name=full_name, email=email, password=password, sex=sex)
    if not user:
        return render(
            request,
            "register.html",
            {
                "page": "auth",
                "error": "Email gia registrata. Prova ad accedere.",
            },
        )

    request.session["user_id"] = user.id
    return RedirectResponse(url="/", status_code=303)


@app.get("/login")
def login_page(request: Request):
    if require_user_id(request):
        return RedirectResponse(url="/", status_code=302)
    return render(request, "login.html", {"page": "auth", "error": None})


@app.post("/login")
def login_action(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
):
    with get_session() as session:
        user = authenticate_user(session, email=email, password=password)

    if not user:
        return render(
            request,
            "login.html",
            {
                "page": "auth",
                "error": "Credenziali non valide.",
            },
        )

    request.session["user_id"] = user.id
    return RedirectResponse(url="/", status_code=303)


@app.post("/api/login")
def api_login(request: Request, payload: LoginPayload):
    with get_session() as session:
        user = authenticate_user(session, email=payload.email, password=payload.password)

    if not user:
        return JSONResponse(
            {"ok": False, "error": "Credenziali non valide."},
            status_code=401,
        )

    request.session["user_id"] = user.id
    return JSONResponse(
        {
            "ok": True,
            "user": {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "sex": user.sex,
            },
        },
        status_code=200,
    )


@app.post("/logout")
def logout_action(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)


@app.get("/today")
def today_page(request: Request):
    user_id = require_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    with get_session() as session:
        workouts = [w for w in list_workouts(session, user_id=user_id) if w.active]
        planned_today = list_planned_workouts_for_day(session, user_id=user_id, day=date.today())
        sessions = list_today_sessions(session, user_id=user_id, day=date.today())

    planned_lookup = {item["workout"].id: item["schedule"].id for item in planned_today}

    return render(
        request,
        "today.html",
        {
            "workouts": workouts,
            "planned_today": planned_today,
            "planned_lookup": planned_lookup,
            "sessions": sessions,
            "today": date.today(),
            "page": "today",
        },
    )


@app.post("/sessions")
def create_session_action(
    request: Request,
    workout_id: int = Form(...),
    schedule_id: str | None = Form(default=None),
    session_date: str | None = Form(default=None),
    duration_minutes: int | None = Form(default=None),
    calories_burned: int | None = Form(default=None),
    notes: str | None = Form(default=None),
    completed: str | None = Form(default=None),
):
    user_id = require_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    parsed_date = date.today()
    if session_date:
        parsed_date = date.fromisoformat(session_date)
    parsed_schedule_id = int(schedule_id) if schedule_id and schedule_id.isdigit() else None

    with get_session() as session:
        try:
            add_session(
                session=session,
                user_id=user_id,
                workout_id=workout_id,
                schedule_id=parsed_schedule_id,
                session_date=parsed_date,
                duration_minutes=duration_minutes,
                calories_burned=calories_burned,
                notes=notes,
                completed=completed is not None,
            )
        except ValueError:
            pass
    return RedirectResponse(url="/today", status_code=303)


@app.get("/workouts")
def workouts_page(request: Request):
    user_id = require_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    with get_session() as session:
        workouts = list_workouts(session, user_id=user_id)
        exercise_catalog = list_exercise_catalog(session)

    enriched_workouts = []
    for workout in workouts:
        details = parse_workout_details(workout)
        enriched_workouts.append({"workout": workout, "details": details})

    return render(
        request,
        "workouts.html",
        {
            "workouts": enriched_workouts,
            "exercise_catalog_json": json.dumps(
                [
                    {
                        "id": item.id,
                        "sport_type": item.sport_type,
                        "name": item.name,
                        "body_zone": item.body_zone,
                    }
                    for item in exercise_catalog
                ],
                ensure_ascii=True,
            ),
            "sport_options": SPORT_OPTIONS,
            "course_options": COURSE_OPTIONS,
            "page": "workouts",
        },
    )


@app.post("/workouts")
def create_workout_action(
    request: Request,
    name: str = Form(...),
    sport_type: str = Form(...),
    estimated_minutes: int = Form(...),
    course_name: str | None = Form(default=None),
    phases_json: str | None = Form(default=None),
):
    user_id = require_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    phases = _parse_phases_json(phases_json)

    with get_session() as session:
        create_workout(
            session=session,
            user_id=user_id,
            name=name,
            sport_type=sport_type,
            estimated_minutes=estimated_minutes,
            course_name=course_name,
            phases=phases,
        )
    return RedirectResponse(url="/workouts", status_code=303)


@app.get("/calendar")
def calendar_page(request: Request, month: str | None = None):
    user_id = require_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    month_date = _month_start(month)
    cal = calendar.Calendar(firstweekday=0)
    weeks = cal.monthdatescalendar(month_date.year, month_date.month)

    prev_month = (month_date.replace(day=1) - timedelta(days=1)).replace(day=1)
    next_month = (month_date.replace(day=28) + timedelta(days=4)).replace(day=1)

    with get_session() as session:
        workouts = [w for w in list_workouts(session, user_id=user_id) if w.active]
        occurrences = list_calendar_occurrences_for_month(session, user_id=user_id, month=month_date)

    holiday_map = {k.isoformat(): v for k, v in italy_holidays(month_date.year).items()}

    return render(
        request,
        "calendar.html",
        {
            "page": "calendar",
            "month_date": month_date,
            "weeks": weeks,
            "occurrences": occurrences,
            "holiday_map": holiday_map,
            "workouts": workouts,
            "prev_month": prev_month.strftime("%Y-%m"),
            "next_month": next_month.strftime("%Y-%m"),
            "weekday_labels": ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"],
        },
    )


@app.post("/schedules")
def create_schedule_action(
    request: Request,
    workout_id: int = Form(...),
    start_date: str = Form(...),
    recurrence_type: str = Form("once"),
    recurrence_days: list[str] | None = Form(default=None),
    end_mode: str = Form("none"),
    end_after_weeks: int | None = Form(default=None),
    end_date: str | None = Form(default=None),
):
    user_id = require_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    selected_days = []
    for raw in recurrence_days or []:
        try:
            day = int(raw)
        except ValueError:
            continue
        if 0 <= day <= 6:
            selected_days.append(day)

    resolved_end_date = date.fromisoformat(end_date) if end_mode == "date" and end_date else None
    resolved_end_weeks = end_after_weeks if end_mode == "weeks" else None
    start = date.fromisoformat(start_date)

    with get_session() as session:
        create_schedule(
            session=session,
            user_id=user_id,
            workout_id=workout_id,
            start_date=start,
            recurrence_type=recurrence_type,
            recurrence_days=selected_days,
            end_after_weeks=resolved_end_weeks,
            end_date=resolved_end_date,
        )
    return RedirectResponse(url=f"/calendar?month={start.strftime('%Y-%m')}", status_code=303)


@app.post("/calendar/remove")
def remove_calendar_occurrence_action(
    request: Request,
    schedule_id: int = Form(...),
    occurrence_date: str = Form(...),
    scope: str = Form("single"),
):
    user_id = require_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    day = date.fromisoformat(occurrence_date)
    with get_session() as session:
        remove_schedule_occurrence(
            session=session,
            user_id=user_id,
            schedule_id=schedule_id,
            occurrence_date=day,
            scope=scope,
        )

    return RedirectResponse(url=f"/calendar?month={day.strftime('%Y-%m')}", status_code=303)


@app.post("/workouts/{workout_id}/toggle")
def toggle_workout(request: Request, workout_id: int):
    user_id = require_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    with get_session() as session:
        toggle_workout_active(session, user_id=user_id, workout_id=workout_id)
    return RedirectResponse(url="/workouts", status_code=303)


@app.post("/workouts/{workout_id}/delete")
def delete_workout_action(request: Request, workout_id: int):
    user_id = require_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    with get_session() as session:
        delete_workout(session, user_id=user_id, workout_id=workout_id)
    return RedirectResponse(url="/workouts", status_code=303)


@app.get("/dashboard")
def dashboard_page(request: Request):
    user_id = require_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    with get_session() as session:
        metrics = dashboard_metrics(session, user_id=user_id)
    return render(
        request,
        "dashboard.html",
        {"metrics": metrics, "page": "dashboard"},
    )
