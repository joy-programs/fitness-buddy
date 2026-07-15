"""
models.py — SQLAlchemy ORM models
----------------------------------
Defines all database tables:
  - UserProfile    : user fitness profile
  - HabitRecord    : daily habit tracking entries
  - WorkoutHistory : log of AI-generated workouts
  - ChatMessage    : conversation history per session
"""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
)
from sqlalchemy.sql import func
from backend.database import Base


class UserProfile(Base):
    """Stores a single user's fitness profile information."""
    __tablename__ = "user_profiles"

    id               = Column(Integer, primary_key=True, index=True)
    name             = Column(String(100), nullable=False, default="Fitness Buddy User")
    age              = Column(Integer, nullable=True)
    gender           = Column(String(20), nullable=True)   # male / female / other
    height_cm        = Column(Float, nullable=True)
    weight_kg        = Column(Float, nullable=True)

    # Fitness attributes
    fitness_level    = Column(String(20), default="beginner")   # beginner / intermediate / advanced
    fitness_goal     = Column(String(100), default="general_fitness")
    # Goals: weight_loss | muscle_gain | general_fitness | stamina | flexibility | active_lifestyle
    workout_duration = Column(Integer, default=30)              # preferred minutes per session
    equipment        = Column(String(200), default="no_equipment")
    # Equipment: no_equipment | resistance_bands | dumbbells | basic_home

    # Lifestyle
    activity_level   = Column(String(30), default="sedentary")
    # sedentary | lightly_active | moderately_active | very_active
    dietary_pref     = Column(String(30), default="non_vegetarian")
    # vegetarian | non_vegetarian | vegan

    created_at       = Column(DateTime(timezone=True), server_default=func.now())
    updated_at       = Column(DateTime(timezone=True), onupdate=func.now())


class HabitRecord(Base):
    """Tracks daily habits for a user profile."""
    __tablename__ = "habit_records"

    id               = Column(Integer, primary_key=True, index=True)
    profile_id       = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    date             = Column(String(10), nullable=False)   # ISO date: YYYY-MM-DD

    workout_done     = Column(Boolean, default=False)
    water_goal_met   = Column(Boolean, default=False)
    healthy_meal     = Column(Boolean, default=False)
    good_sleep       = Column(Boolean, default=False)
    daily_movement   = Column(Boolean, default=False)

    created_at       = Column(DateTime(timezone=True), server_default=func.now())
    updated_at       = Column(DateTime(timezone=True), onupdate=func.now())


class WorkoutHistory(Base):
    """Logs AI-generated workouts so users can revisit them."""
    __tablename__ = "workout_history"

    id               = Column(Integer, primary_key=True, index=True)
    profile_id       = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    workout_json     = Column(Text, nullable=False)   # JSON string of the full workout
    fitness_goal     = Column(String(100), nullable=True)
    duration_min     = Column(Integer, nullable=True)
    equipment        = Column(String(200), nullable=True)
    created_at       = Column(DateTime(timezone=True), server_default=func.now())


class ChatMessage(Base):
    """Stores the chat conversation history for a session."""
    __tablename__ = "chat_messages"

    id               = Column(Integer, primary_key=True, index=True)
    session_id       = Column(String(100), nullable=False, index=True)
    profile_id       = Column(Integer, nullable=True)      # optional link to profile
    role             = Column(String(10), nullable=False)  # "user" or "assistant"
    content          = Column(Text, nullable=False)
    created_at       = Column(DateTime(timezone=True), server_default=func.now())
