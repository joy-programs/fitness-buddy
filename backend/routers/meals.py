"""
routers/meals.py — Healthy Meal Suggestion API
-----------------------------------------------
Endpoint:
  POST /api/meals/suggest — generate a day's meal plan using Granite
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend import models
from backend.schemas import MealRequest, MealResponse
from backend.agent_instructions import build_system_prompt, build_profile_context
import backend.watsonx_service as wxs

router = APIRouter(prefix="/api/meals", tags=["Meals"])


@router.post("/suggest", response_model=MealResponse)
def suggest_meals(payload: MealRequest, db: Session = Depends(get_db)):
    """
    Generate a personalised day's meal plan using IBM Granite.

    Pulls dietary preference and fitness goal from the saved profile
    if profile_id is provided; otherwise uses the request payload.
    """
    dietary_pref  = payload.dietary_pref
    fitness_goal  = payload.fitness_goal
    profile_context = ""

    if payload.profile_id:
        profile = db.query(models.UserProfile).filter(
            models.UserProfile.id == payload.profile_id
        ).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found.")
        dietary_pref    = profile.dietary_pref
        fitness_goal    = profile.fitness_goal
        profile_context = build_profile_context(profile)

    system_prompt = build_system_prompt(profile_context)

    try:
        meals = wxs.generate_meal_suggestions(
            system_prompt=system_prompt,
            dietary_pref=dietary_pref,
            fitness_goal=fitness_goal,
            special_request=payload.special_request,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc)
        )

    return MealResponse(meals=meals)
