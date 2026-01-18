"""User management router."""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from backend.db import get_session
from backend.models import User
from backend.schemas import UserEnsureResponse

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("/ensure", response_model=UserEnsureResponse)
def ensure_user(
    user_id: str = None,
    session: Session = Depends(get_session)
):
    """
    Ensure user exists, create if not.
    Returns: {user_id}
    """
    if user_id:
        # Check if user exists
        user = session.get(User, user_id)
        if user:
            return UserEnsureResponse(user_id=user.id)
    
    # Create new user
    user = User(id=str(uuid.uuid4()))
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return UserEnsureResponse(user_id=user.id)
