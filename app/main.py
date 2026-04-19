from datetime import date
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.db import get_session, init_db
from app.services import (
    add_session,
    create_workout,
    dashboard_metrics,
    delete_workout,
    list_today_sessions,
    list_workouts,
    toggle_workout_active,
)


app = FastAPI(title="MyFit Journal")

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/")
def home(request: Request):
    user_agent = (request.headers.get("user-agent") or "").lower()
    if "iphone" in user_agent or "android" in user_agent:
        return RedirectResponse(url="/today", status_code=302)
    return RedirectResponse(url="/dashboard", status_code=302)


@app.get("/today")
def today_page(request: Request):
    with get_session() as session:
        workouts = [w for w in list_workouts(session) if w.active]
        sessions = list_today_sessions(session, date.today())
    return templates.TemplateResponse(
        "today.html",
        {
            "request": request,
            "workouts": workouts,
            "sessions": sessions,
            "today": date.today(),
            "page": "today",
        },
    )


@app.post("/sessions")
def create_session(
    workout_id: int = Form(...),
    session_date: str | None = Form(default=None),
    duration_minutes: int | None = Form(default=None),
    calories_burned: int | None = Form(default=None),
    notes: str | None = Form(default=None),
    completed: str | None = Form(default=None),
):
    parsed_date = date.today()
    if session_date:
        parsed_date = date.fromisoformat(session_date)
    with get_session() as session:
        add_session(
            session=session,
            workout_id=workout_id,
            session_date=parsed_date,
            duration_minutes=duration_minutes,
            calories_burned=calories_burned,
            notes=notes,
            completed=completed is not None,
        )
    return RedirectResponse(url="/today", status_code=303)


@app.get("/workouts")
def workouts_page(request: Request):
    with get_session() as session:
        workouts = list_workouts(session)
    return templates.TemplateResponse(
        "workouts.html",
        {"request": request, "workouts": workouts, "page": "workouts"},
    )


@app.post("/workouts")
def create_workout_action(
    name: str = Form(...),
    category: str = Form(...),
    target_area: str = Form(...),
    estimated_minutes: int = Form(...),
    exercise_block: str = Form(...),
):
    with get_session() as session:
        create_workout(
            session=session,
            name=name,
            category=category,
            target_area=target_area,
            estimated_minutes=estimated_minutes,
            exercise_block=exercise_block,
        )
    return RedirectResponse(url="/workouts", status_code=303)


@app.post("/workouts/{workout_id}/toggle")
def toggle_workout(workout_id: int):
    with get_session() as session:
        toggle_workout_active(session, workout_id)
    return RedirectResponse(url="/workouts", status_code=303)


@app.post("/workouts/{workout_id}/delete")
def delete_workout_action(workout_id: int):
    with get_session() as session:
        delete_workout(session, workout_id)
    return RedirectResponse(url="/workouts", status_code=303)


@app.get("/dashboard")
def dashboard_page(request: Request):
    with get_session() as session:
        metrics = dashboard_metrics(session)
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "metrics": metrics, "page": "dashboard"},
    )
