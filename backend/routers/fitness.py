"""
routers/fitness.py — BMI and Fitness Calculations API
------------------------------------------------------
Endpoint:
  POST /api/fitness/bmi — calculate BMI from height and weight
  GET  /api/fitness/bmi — calculate BMI from query params
"""

from fastapi import APIRouter, HTTPException, status
from backend.schemas import BMIRequest, BMIResponse
from backend.fitness_utils import calculate_bmi

router = APIRouter(prefix="/api/fitness", tags=["Fitness Calculations"])


@router.post("/bmi", response_model=BMIResponse)
def bmi_from_body(payload: BMIRequest):
    """Calculate BMI from a JSON request body."""
    return _calculate(payload.height_cm, payload.weight_kg)


@router.get("/bmi", response_model=BMIResponse)
def bmi_from_query(height_cm: float, weight_kg: float):
    """Calculate BMI from query parameters (convenient for dashboard use)."""
    if height_cm <= 50 or height_cm >= 300:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="height_cm must be between 50 and 300."
        )
    if weight_kg <= 10 or weight_kg >= 500:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="weight_kg must be between 10 and 500."
        )
    return _calculate(height_cm, weight_kg)


def _calculate(height_cm: float, weight_kg: float) -> BMIResponse:
    """Shared BMI calculation logic."""
    try:
        result = calculate_bmi(height_cm, weight_kg)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc)
        )
    return BMIResponse(**result)
