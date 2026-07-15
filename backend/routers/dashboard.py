"""
routers/dashboard.py — Dashboard Data Aggregator
-------------------------------------------------
Endpoint:
  GET /api/dashboard/{profile_id} — return all dashboard widgets in one call
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date as date_type

from backend.database import get_db
from backend import models
from backend.schemas import DashboardResponse, ProfileResponse, BMIResponse, HabitResponse
from backend.fitness_utils import calculate_bmi, streak_from_habits
from backend.agent_instructions import build_system_prompt, build_profile_context
import backend.watsonx_service as wxs

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/{profile_id}", response_model=DashboardResponse)
def get_dashboard(profile_id: int, db: Session = Depends(get_db)):
    """
    Aggregate all information needed for the fitness dashboard in one request:
    - Profile summary
    - BMI (if height/weight available)
    - Today's habit record
    - Streak count
    - Daily motivation message
    - A quick healthy tip
    """
    # ── Load profile ──────────────────────────────────────────
    profile = db.query(models.UserProfile).filter(
        models.UserProfile.id == profile_id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")

    profile_resp = ProfileResponse.model_validate(profile)

    # ── Calculate BMI if data available ───────────────────────
    bmi_resp = None
    if profile.height_cm and profile.weight_kg:
        try:
            bmi_data = calculate_bmi(profile.height_cm, profile.weight_kg)
            bmi_resp = BMIResponse(**bmi_data)
        except ValueError:
            pass

    # ── Today's habits ────────────────────────────────────────
    today = str(date_type.today())
    habit = db.query(models.HabitRecord).filter(
        models.HabitRecord.profile_id == profile_id,
        models.HabitRecord.date == today,
    ).first()

    if habit:
        fields = [
            habit.workout_done, habit.water_goal_met,
            habit.healthy_meal, habit.good_sleep, habit.daily_movement,
        ]
        pct = round((sum(1 for f in fields if f) / 5) * 100, 1)
    else:
        pct = 0.0

    # Streak
    rows = (
        db.query(models.HabitRecord.date)
        .filter(
            models.HabitRecord.profile_id == profile_id,
            (
                models.HabitRecord.workout_done |
                models.HabitRecord.water_goal_met |
                models.HabitRecord.healthy_meal |
                models.HabitRecord.good_sleep |
                models.HabitRecord.daily_movement
            )
        ).all()
    )
    streak = streak_from_habits([r.date for r in rows])

    habit_resp = HabitResponse(
        id=habit.id if habit else 0,
        profile_id=profile_id,
        date=today,
        workout_done=habit.workout_done if habit else False,
        water_goal_met=habit.water_goal_met if habit else False,
        healthy_meal=habit.healthy_meal if habit else False,
        good_sleep=habit.good_sleep if habit else False,
        daily_movement=habit.daily_movement if habit else False,
        completion_pct=pct,
        streak=streak,
    )

    # ── Daily motivation via Granite ──────────────────────────
    profile_context = build_profile_context(profile)
    system_prompt   = build_system_prompt(profile_context)

    try:
        motiv = wxs.generate_motivation(system_prompt=system_prompt)
        motivation_msg = motiv.get("message", "Every workout makes you stronger!")
        quick_tip      = motiv.get("tip", "Stay hydrated throughout the day.")
    except RuntimeError:
        motivation_msg = "Every workout makes you stronger — keep going!"
        quick_tip      = "Drink a glass of water right now."

    return DashboardResponse(
        profile=profile_resp,
        bmi=bmi_resp,
        today_habits=habit_resp,
        streak=streak,
        motivation=motivation_msg,
        quick_tip=quick_tip,
    )
