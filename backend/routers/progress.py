"""Progress and readiness tracking router."""

import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from backend.db import get_session
from backend.models import UserReadinessSnapshot
from backend.schemas import ProgressOverviewResponse

router = APIRouter(prefix="/api/progress", tags=["progress"])


@router.get("/overview", response_model=ProgressOverviewResponse)
def get_progress_overview(
    user_id: str,
    job_spec_id: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """Get progress overview with readiness score and trend."""
    # Get latest snapshot
    query = select(UserReadinessSnapshot).where(UserReadinessSnapshot.user_id == user_id)
    if job_spec_id:
        query = query.where(UserReadinessSnapshot.job_spec_id == job_spec_id)
    
    snapshots = list(session.exec(
        query.order_by(UserReadinessSnapshot.timestamp.desc())
    ).all())
    
    latest_snapshot = snapshots[0] if snapshots else None
    
    # Build trend (last 10 snapshots)
    trend = []
    for snap in snapshots[:10]:
        trend.append({
            "timestamp": snap.timestamp.isoformat(),
            "readiness_score": snap.readiness_score,
            "cv_score": snap.cv_score,
            "interview_score": snap.interview_score,
            "practice_score": snap.practice_score
        })
    
    # Build breakdown
    breakdown = {}
    if latest_snapshot:
        breakdown = json.loads(latest_snapshot.breakdown_json or "{}")
    else:
        breakdown = {
            "cv_score": 0.0,
            "interview_score": 0.0,
            "practice_score": 0.0,
            "weights": {"cv": 0.4, "interview": 0.5, "practice": 0.1}
        }
    
    latest_snapshot_data = None
    if latest_snapshot:
        latest_snapshot_data = {
            "timestamp": latest_snapshot.timestamp.isoformat(),
            "readiness_score": latest_snapshot.readiness_score,
            "cv_score": latest_snapshot.cv_score,
            "interview_score": latest_snapshot.interview_score,
            "practice_score": latest_snapshot.practice_score,
            "breakdown": breakdown
        }
    
    return ProgressOverviewResponse(
        latest_snapshot=latest_snapshot_data,
        trend=trend,
        breakdown=breakdown
    )
