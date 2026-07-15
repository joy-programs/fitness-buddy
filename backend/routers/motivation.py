"""
routers/motivation.py — Daily Motivation API
---------------------------------------------
Endpoint:
  POST /api/motivation — generate a motivational message using Granite
  GET  /api/motivation — quick motivation with no request body
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from backend.database import get_db
from backend import models
from backend.schemas import MotivationRequest, MotivationResponse
from backend.agent_instructions import build_system_prompt, build_profile_context
import backend.watsonx_service as wxs

router = APIRouter(prefix="/api/motivation", tags=["Motivation"])


def _get_motivation(
    profile_id: Optional[int],
    context:    Optional[str],
    db: Session,
) -> MotivationResponse:
    """Shared helper used by both GET and POST handlers."""
    profile_context = ""
    if profile_id:
        profile = db.query(models.UserProfile).filter(
            models.UserProfile.id == profile_id
        ).first()
        if profile:
            profile_context = build_profile_context(profile)

    system_prompt = build_system_prompt(profile_context)

    try:
        result = wxs.generate_motivation(system_prompt=system_prompt, context=context)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc)
        )

    return MotivationResponse(
        message=result.get("message", "Keep going — every step forward counts!"),
        tip=result.get("tip"),
    )


@router.get("", response_model=MotivationResponse)
def get_quick_motivation(
    profile_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get a quick motivational message (no request body needed)."""
    return _get_motivation(profile_id=profile_id, context=None, db=db)


@router.post("", response_model=MotivationResponse)
def post_motivation(payload: MotivationRequest, db: Session = Depends(get_db)):
    """Get a contextualised motivational message."""
    return _get_motivation(
        profile_id=payload.profile_id,
        context=payload.context,
        db=db,
    )
