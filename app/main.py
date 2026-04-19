import json
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

from app.auth import build_session_cookie_flags
from app.config import get_settings
from app.constants import BODY_ZONES, COURSE_OPTIONS, SPORT_OPTIONS
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
    list_planned_workouts_for_day,
    list_schedules,
    list_today_sessions,
    list_workouts,
    parse_workout_details,
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


def _parse_exercises_json(raw: str | None) -> list[dict]:
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
        name = str(item.get("name", "")).strip()
        if not name:
            continue
        cleaned.append(
            {
                "name": name,
                "mode": str(item.get("mode", "single")),
                "sets": int(item.get("sets") or 0) or None,
                "reps": int(item.get("reps") or 0) or None,
                "duration_minutes": int(item.get("duration_minutes") or 0) or None,
                "objective": str(item.get("objective", "")).strip() or None,
                "body_zone": str(item.get("body_zone", "full_body")).strip() or "full_body",
            }
        )
    return cleaned


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
        schedules = list_schedules(session, user_id=user_id)

    enriched_workouts = []
    for workout in workouts:
        details = parse_workout_details(workout)
        enriched_workouts.append({"workout": workout, "details": details})

    return render(
        request,
        "workouts.html",
        {
            "workouts": enriched_workouts,
            "schedules": schedules,
            "sport_options": SPORT_OPTIONS,
            "course_options": COURSE_OPTIONS,
            "body_zones": BODY_ZONES,
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
    warmup_minutes: int | None = Form(default=None),
    warmup_notes: str | None = Form(default=None),
    cooldown_minutes: int | None = Form(default=None),
    cooldown_notes: str | None = Form(default=None),
    exercises_json: str | None = Form(default=None),
):
    user_id = require_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    warmup = {"minutes": warmup_minutes, "notes": (warmup_notes or "").strip() or None}
    cooldown = {"minutes": cooldown_minutes, "notes": (cooldown_notes or "").strip() or None}
    exercises = _parse_exercises_json(exercises_json)

    with get_session() as session:
        create_workout(
            session=session,
            user_id=user_id,
            name=name,
            sport_type=sport_type,
            estimated_minutes=estimated_minutes,
            course_name=course_name,
            warmup=warmup,
            cooldown=cooldown,
            exercises=exercises,
        )
    return RedirectResponse(url="/workouts", status_code=303)


@app.post("/schedules")
def create_schedule_action(
    request: Request,
    workout_id: int = Form(...),
    start_date: str = Form(...),
    recurrence_type: str = Form("once"),
    repeat_weeks: int | None = Form(default=None),
):
    user_id = require_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    with get_session() as session:
        create_schedule(
            session=session,
            user_id=user_id,
            workout_id=workout_id,
            start_date=date.fromisoformat(start_date),
            recurrence_type=recurrence_type,
            repeat_weeks=repeat_weeks,
        )
    return RedirectResponse(url="/workouts", status_code=303)


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
