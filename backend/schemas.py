"""
schemas.py — Pydantic request & response schemas
-------------------------------------------------
All FastAPI route inputs and outputs are validated through
these Pydantic models. This keeps API contracts explicit and
gives automatic OpenAPI documentation.

Updated for pydantic v2.13+ (Python 3.14 compatible):
  - @validator  → @field_validator (no deprecation warnings)
  - class Config → model_config = ConfigDict(from_attributes=True)
"""

from __future__ import annotations
from typing import Optional, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime


# ── Shared allowed values ─────────────────────────────────────

FITNESS_LEVELS    = ["beginner", "intermediate", "advanced"]
FITNESS_GOALS     = [
    "weight_loss", "muscle_gain", "general_fitness",
    "stamina", "flexibility", "active_lifestyle"
]
EQUIPMENT_OPTIONS = ["no_equipment", "resistance_bands", "dumbbells", "basic_home"]
ACTIVITY_LEVELS   = ["sedentary", "lightly_active", "moderately_active", "very_active"]
DIETARY_PREFS     = ["vegetarian", "non_vegetarian", "vegan"]


# ── User Profile ──────────────────────────────────────────────

class ProfileCreate(BaseModel):
    """Schema for creating or fully updating a fitness profile."""
    name:             str   = Field(default="Fitness Buddy User", max_length=100)
    age:              Optional[int]   = Field(None, ge=10, le=100)
    gender:           Optional[str]   = Field(None)
    height_cm:        Optional[float] = Field(None, gt=50, lt=300, description="Height in centimetres")
    weight_kg:        Optional[float] = Field(None, gt=10, lt=500, description="Weight in kilograms")
    fitness_level:    str   = Field(default="beginner")
    fitness_goal:     str   = Field(default="general_fitness")
    workout_duration: int   = Field(default=30, ge=5, le=180, description="Preferred session duration in minutes")
    equipment:        str   = Field(default="no_equipment")
    activity_level:   str   = Field(default="sedentary")
    dietary_pref:     str   = Field(default="non_vegetarian")

    @field_validator("fitness_level")
    @classmethod
    def validate_fitness_level(cls, v: str) -> str:
        if v not in FITNESS_LEVELS:
            raise ValueError(f"fitness_level must be one of {FITNESS_LEVELS}")
        return v

    @field_validator("fitness_goal")
    @classmethod
    def validate_fitness_goal(cls, v: str) -> str:
        if v not in FITNESS_GOALS:
            raise ValueError(f"fitness_goal must be one of {FITNESS_GOALS}")
        return v

    @field_validator("equipment")
    @classmethod
    def validate_equipment(cls, v: str) -> str:
        if v not in EQUIPMENT_OPTIONS:
            raise ValueError(f"equipment must be one of {EQUIPMENT_OPTIONS}")
        return v

    @field_validator("activity_level")
    @classmethod
    def validate_activity_level(cls, v: str) -> str:
        if v not in ACTIVITY_LEVELS:
            raise ValueError(f"activity_level must be one of {ACTIVITY_LEVELS}")
        return v

    @field_validator("dietary_pref")
    @classmethod
    def validate_dietary_pref(cls, v: str) -> str:
        if v not in DIETARY_PREFS:
            raise ValueError(f"dietary_pref must be one of {DIETARY_PREFS}")
        return v


class ProfileUpdate(ProfileCreate):
    """All fields optional for PATCH-style partial updates."""
    name:             Optional[str]   = None
    fitness_level:    Optional[str]   = None
    fitness_goal:     Optional[str]   = None
    workout_duration: Optional[int]   = None
    equipment:        Optional[str]   = None
    activity_level:   Optional[str]   = None
    dietary_pref:     Optional[str]   = None


class ProfileResponse(BaseModel):
    """What the API returns after a profile read/create/update."""
    model_config = ConfigDict(from_attributes=True)

    id:               int
    name:             str
    age:              Optional[int]
    gender:           Optional[str]
    height_cm:        Optional[float]
    weight_kg:        Optional[float]
    fitness_level:    str
    fitness_goal:     str
    workout_duration: int
    equipment:        str
    activity_level:   str
    dietary_pref:     str
    created_at:       Optional[datetime]
    updated_at:       Optional[datetime]


# ── Chat ──────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message:    str        = Field(..., min_length=1, max_length=2000)
    session_id: str        = Field(..., min_length=1, max_length=100)
    profile_id: Optional[int] = None


class ChatResponse(BaseModel):
    reply:      str
    session_id: str


# ── Workout Generator ─────────────────────────────────────────

class WorkoutRequest(BaseModel):
    profile_id:    Optional[int]  = None
    fitness_level: str            = Field(default="beginner")
    fitness_goal:  str            = Field(default="general_fitness")
    duration_min:  int            = Field(default=30, ge=5, le=120)
    equipment:     str            = Field(default="no_equipment")
    modification:  Optional[str]  = None   # e.g. "make it easier", "no jumping"

    @field_validator("fitness_level")
    @classmethod
    def validate_fitness_level(cls, v: str) -> str:
        if v not in FITNESS_LEVELS:
            raise ValueError(f"fitness_level must be one of {FITNESS_LEVELS}")
        return v

    @field_validator("fitness_goal")
    @classmethod
    def validate_fitness_goal(cls, v: str) -> str:
        if v not in FITNESS_GOALS:
            raise ValueError(f"fitness_goal must be one of {FITNESS_GOALS}")
        return v


class WorkoutResponse(BaseModel):
    workout:  Any              # structured JSON from Granite (dict) or fallback string
    saved_id: Optional[int] = None


# ── BMI Calculator ────────────────────────────────────────────

class BMIRequest(BaseModel):
    height_cm: float = Field(..., gt=50, lt=300, description="Height in centimetres")
    weight_kg: float = Field(..., gt=10, lt=500, description="Weight in kilograms")


class BMIResponse(BaseModel):
    bmi:           float
    category:      str
    healthy_range: str
    disclaimer:    str


# ── Meal Suggestions ──────────────────────────────────────────

class MealRequest(BaseModel):
    profile_id:      Optional[int] = None
    dietary_pref:    str           = Field(default="non_vegetarian")
    fitness_goal:    str           = Field(default="general_fitness")
    special_request: Optional[str] = None   # e.g. "high protein", "quick meal", "hostel-friendly"

    @field_validator("dietary_pref")
    @classmethod
    def validate_dietary_pref(cls, v: str) -> str:
        if v not in DIETARY_PREFS:
            raise ValueError(f"dietary_pref must be one of {DIETARY_PREFS}")
        return v


class MealResponse(BaseModel):
    meals: Any   # structured JSON from Granite or fallback string


# ── Motivation ────────────────────────────────────────────────

class MotivationRequest(BaseModel):
    profile_id: Optional[int] = None
    context:    Optional[str] = None   # e.g. "feeling lazy today"


class MotivationResponse(BaseModel):
    message: str
    tip:     Optional[str] = None


# ── Habit Tracker ─────────────────────────────────────────────

class HabitUpdate(BaseModel):
    date:           str  = Field(..., description="ISO date string YYYY-MM-DD")
    workout_done:   Optional[bool] = None
    water_goal_met: Optional[bool] = None
    healthy_meal:   Optional[bool] = None
    good_sleep:     Optional[bool] = None
    daily_movement: Optional[bool] = None


class HabitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:             int
    profile_id:     int
    date:           str
    workout_done:   bool
    water_goal_met: bool
    healthy_meal:   bool
    good_sleep:     bool
    daily_movement: bool
    completion_pct: float   # 0-100
    streak:         int     # consecutive days with at least one habit


# ── Dashboard ─────────────────────────────────────────────────

class DashboardResponse(BaseModel):
    profile:      Optional[ProfileResponse]
    bmi:          Optional[BMIResponse]
    today_habits: Optional[HabitResponse]
    streak:       int
    motivation:   str
    quick_tip:    Optional[str]


# ── Generic error response ────────────────────────────────────

class ErrorResponse(BaseModel):
    detail: str
    code:   Optional[str] = None
