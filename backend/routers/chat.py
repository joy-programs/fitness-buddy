"""
routers/chat.py — AI Fitness Chat API
--------------------------------------
Endpoint:
  POST /api/chat — send a message, receive an AI response

Conversation history is loaded from the database so the
agent can maintain context across turns within a session.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend import models
from backend.schemas import ChatRequest, ChatResponse
from backend.agent_instructions import build_system_prompt, build_profile_context
import backend.watsonx_service as wxs

router = APIRouter(prefix="/api/chat", tags=["Chat"])

# Max history messages to load from DB per session (keeps context manageable)
MAX_HISTORY = 10


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    """
    Send a message to the Fitness Buddy AI and receive a reply.

    - session_id : unique string per browser tab / conversation
    - profile_id : optional; if provided, personalises the AI response
    - message    : the user's text message
    """
    # ── 1. Load profile context (optional) ───────────────────
    profile = None
    if payload.profile_id:
        profile = db.query(models.UserProfile).filter(
            models.UserProfile.id == payload.profile_id
        ).first()
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Profile {payload.profile_id} not found."
            )

    profile_context = build_profile_context(profile)
    system_prompt   = build_system_prompt(profile_context)

    # ── 2. Load conversation history for this session ─────────
    history_rows = (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.session_id == payload.session_id)
        .order_by(models.ChatMessage.created_at.asc())
        .limit(MAX_HISTORY)
        .all()
    )
    history = [{"role": row.role, "content": row.content} for row in history_rows]

    # ── 3. Call IBM Granite ───────────────────────────────────
    try:
        reply = wxs.chat_with_buddy(
            system_prompt=system_prompt,
            user_message=payload.message,
            history=history,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc)
        )

    # ── 4. Persist both turns to the database ─────────────────
    db.add(models.ChatMessage(
        session_id=payload.session_id,
        profile_id=payload.profile_id,
        role="user",
        content=payload.message,
    ))
    db.add(models.ChatMessage(
        session_id=payload.session_id,
        profile_id=payload.profile_id,
        role="assistant",
        content=reply,
    ))
    db.commit()

    return ChatResponse(reply=reply, session_id=payload.session_id)


@router.get("/history/{session_id}")
def get_history(session_id: str, db: Session = Depends(get_db)):
    """Return the conversation history for a given session."""
    rows = (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.session_id == session_id)
        .order_by(models.ChatMessage.created_at.asc())
        .all()
    )
    return [{"role": r.role, "content": r.content, "created_at": r.created_at} for r in rows]
