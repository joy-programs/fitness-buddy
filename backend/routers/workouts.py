"""
routers/workouts.py — Workout Generator API
--------------------------------------------
Endpoints:
  POST /api/workouts/generate   — generate a personalised workout plan
  GET  /api/workouts/history/{profile_id}  — list saved workouts
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import json

from backend.database import get_db
from backend import models
from backend.schemas import WorkoutRequest, WorkoutResponse
from backend.agent_instructions import build_system_prompt, build_profile_context
import backend.watsonx_service as wxs

router = APIRouter(prefix="/api/workouts", tags=["Workouts"])


@router.post("/generate", response_model=WorkoutResponse)
def generate_workout(payload: WorkoutRequest, db: Session = Depends(get_db)):
    """
    Generate a personalised home workout plan using IBM Granite.

    If profile_id is provided, the profile's fitness level, goal,
    duration, and equipment override the payload defaults.
    """
    # ── Resolve effective parameters ──────────────────────────
    fitness_level  = payload.fitness_level
    fitness_goal   = payload.fitness_goal
    duration_min   = payload.duration_min
    equipment      = payload.equipment

    if payload.profile_id:
        profile = db.query(models.UserProfile).filter(
            models.UserProfile.id == payload.profile_id
        ).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found.")

        # Profile values win over payload defaults
        fitness_level = profile.fitness_level
        fitness_goal  = profile.fitness_goal
        duration_min  = payload.duration_min or profile.workout_duration
        equipment     = profile.equipment

        profile_context = build_profile_context(profile)
    else:
        profile_context = ""

    system_prompt = build_system_prompt(profile_context)

    # ── Call Granite to generate the workout ──────────────────
    try:
        workout_data = wxs.generate_workout(
            system_prompt=system_prompt,
            fitness_level=fitness_level,
            fitness_goal=fitness_goal,
            duration_min=duration_min,
            equipment=equipment,
            modification=payload.modification,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc)
        )

    # ── Persist the generated workout to history ──────────────
    saved_id = None
    if payload.profile_id:
        workout_str = json.dumps(workout_data) if isinstance(workout_data, dict) \
                      else str(workout_data)
        record = models.WorkoutHistory(
            profile_id=payload.profile_id,
            workout_json=workout_str,
            fitness_goal=fitness_goal,
            duration_min=duration_min,
            equipment=equipment,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        saved_id = record.id

    return WorkoutResponse(workout=workout_data, saved_id=saved_id)


@router.get("/history/{profile_id}")
def get_workout_history(
    profile_id: int,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """Return the most recent workout history for a profile."""
    records = (
        db.query(models.WorkoutHistory)
        .filter(models.WorkoutHistory.profile_id == profile_id)
        .order_by(models.WorkoutHistory.created_at.desc())
        .limit(limit)
        .all()
    )
    results = []
    for r in records:
        try:
            workout = json.loads(r.workout_json)
        except (json.JSONDecodeError, TypeError):
            workout = r.workout_json
        results.append({
            "id":          r.id,
            "workout":     workout,
            "fitness_goal": r.fitness_goal,
            "duration_min": r.duration_min,
            "equipment":   r.equipment,
            "created_at":  r.created_at,
        })
    return results
