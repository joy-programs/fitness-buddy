"""
routers/profile.py — Fitness Profile API
-----------------------------------------
Endpoints:
  POST   /api/profile        — create a new profile
  GET    /api/profile/{id}   — fetch a profile by ID
  PUT    /api/profile/{id}   — full update
  PATCH  /api/profile/{id}   — partial update
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend import models
from backend.schemas import ProfileCreate, ProfileUpdate, ProfileResponse

router = APIRouter(prefix="/api/profile", tags=["Profile"])


@router.post("", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
def create_profile(payload: ProfileCreate, db: Session = Depends(get_db)):
    """Create a new fitness profile."""
    # Map Pydantic model → SQLAlchemy model
    profile = models.UserProfile(**payload.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/{profile_id}", response_model=ProfileResponse)
def get_profile(profile_id: int, db: Session = Depends(get_db)):
    """Retrieve a fitness profile by its ID."""
    profile = db.query(models.UserProfile).filter(
        models.UserProfile.id == profile_id
    ).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile with id={profile_id} not found."
        )
    return profile


@router.put("/{profile_id}", response_model=ProfileResponse)
def update_profile(
    profile_id: int,
    payload: ProfileCreate,
    db: Session = Depends(get_db)
):
    """Fully replace a fitness profile."""
    profile = db.query(models.UserProfile).filter(
        models.UserProfile.id == profile_id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")

    for field, value in payload.model_dump().items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile


@router.patch("/{profile_id}", response_model=ProfileResponse)
def partial_update_profile(
    profile_id: int,
    payload: ProfileUpdate,
    db: Session = Depends(get_db)
):
    """Partially update a fitness profile (only provided fields are updated)."""
    profile = db.query(models.UserProfile).filter(
        models.UserProfile.id == profile_id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")

    # model_dump(exclude_unset=True) only includes fields the user actually sent
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile
