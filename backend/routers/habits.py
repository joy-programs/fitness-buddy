"""
routers/habits.py — Daily Habit Tracker API
--------------------------------------------
Endpoints:
  GET   /api/habits/{profile_id}?date=YYYY-MM-DD  — get today's habits
  POST  /api/habits/{profile_id}                  — upsert today's habits
  GET   /api/habits/{profile_id}/streak            — get consistency streak
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date as date_type

from backend.database import get_db
from backend import models
from backend.schemas import HabitUpdate, HabitResponse
from backend.fitness_utils import streak_from_habits

router = APIRouter(prefix="/api/habits", tags=["Habits"])


def _compute_completion(habit: models.HabitRecord) -> float:
    """Return percentage of habits completed for a record (0–100)."""
    fields = [
        habit.workout_done, habit.water_goal_met,
        habit.healthy_meal, habit.good_sleep, habit.daily_movement,
    ]
    completed = sum(1 for f in fields if f)
    return round((completed / len(fields)) * 100, 1)


def _get_streak(profile_id: int, db: Session) -> int:
    """Compute the current streak for a profile."""
    rows = (
        db.query(models.HabitRecord.date)
        .filter(
            models.HabitRecord.profile_id == profile_id,
            # Only count days where at least one habit was done
            (
                models.HabitRecord.workout_done |
                models.HabitRecord.water_goal_met |
                models.HabitRecord.healthy_meal |
                models.HabitRecord.good_sleep |
                models.HabitRecord.daily_movement
            )
        )
        .all()
    )
    dates = [r.date for r in rows]
    return streak_from_habits(dates)


@router.get("/{profile_id}", response_model=HabitResponse)
def get_habits(
    profile_id: int,
    date: str = None,
    db: Session = Depends(get_db),
):
    """
    Retrieve the habit record for a given profile and date.
    Defaults to today's date if not specified.
    Creates an empty record if one doesn't exist yet.
    """
    target_date = date or str(date_type.today())

    # Verify profile exists
    profile = db.query(models.UserProfile).filter(
        models.UserProfile.id == profile_id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")

    habit = db.query(models.HabitRecord).filter(
        models.HabitRecord.profile_id == profile_id,
        models.HabitRecord.date == target_date,
    ).first()

    if not habit:
        # Return a clean empty record (not yet persisted)
        habit = models.HabitRecord(
            id=0,
            profile_id=profile_id,
            date=target_date,
            workout_done=False,
            water_goal_met=False,
            healthy_meal=False,
            good_sleep=False,
            daily_movement=False,
        )

    return HabitResponse(
        id=habit.id,
        profile_id=habit.profile_id,
        date=habit.date,
        workout_done=habit.workout_done,
        water_goal_met=habit.water_goal_met,
        healthy_meal=habit.healthy_meal,
        good_sleep=habit.good_sleep,
        daily_movement=habit.daily_movement,
        completion_pct=_compute_completion(habit),
        streak=_get_streak(profile_id, db),
    )


@router.post("/{profile_id}", response_model=HabitResponse)
def upsert_habits(
    profile_id: int,
    payload: HabitUpdate,
    db: Session = Depends(get_db),
):
    """
    Create or update a habit record for a profile and date.
    Only the fields included in the request body are updated.
    """
    profile = db.query(models.UserProfile).filter(
        models.UserProfile.id == profile_id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")

    habit = db.query(models.HabitRecord).filter(
        models.HabitRecord.profile_id == profile_id,
        models.HabitRecord.date == payload.date,
    ).first()

    if not habit:
        habit = models.HabitRecord(profile_id=profile_id, date=payload.date)
        db.add(habit)

    # Apply only the fields that were provided
    update_data = payload.model_dump(exclude_unset=True, exclude={"date"})
    for field, value in update_data.items():
        if value is not None:
            setattr(habit, field, value)

    db.commit()
    db.refresh(habit)

    return HabitResponse(
        id=habit.id,
        profile_id=habit.profile_id,
        date=habit.date,
        workout_done=habit.workout_done,
        water_goal_met=habit.water_goal_met,
        healthy_meal=habit.healthy_meal,
        good_sleep=habit.good_sleep,
        daily_movement=habit.daily_movement,
        completion_pct=_compute_completion(habit),
        streak=_get_streak(profile_id, db),
    )


@router.get("/{profile_id}/streak")
def get_streak(profile_id: int, db: Session = Depends(get_db)):
    """Return the current habit streak for a profile."""
    profile = db.query(models.UserProfile).filter(
        models.UserProfile.id == profile_id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")
    return {"profile_id": profile_id, "streak": _get_streak(profile_id, db)}
