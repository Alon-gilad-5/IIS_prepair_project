"""Readiness score calculation and snapshots."""

import json
from typing import Dict, Any, Optional
from datetime import datetime
from sqlmodel import Session, select
from backend.models import (
    UserReadinessSnapshot, CVAnalysisResult, InterviewSession, InterviewTurn, JobSpec
)


def compute_readiness_snapshot(
    session: Session,
    user_id: str,
    job_spec_id: Optional[str],
    context: str = "cv_analysis"  # "cv_analysis" | "interview_end"
) -> UserReadinessSnapshot:
    """
    Compute and persist readiness snapshot.
    
    Formula:
    - cv_score: 40% (from cv_analysis_results)
    - interview_score: 50% (average of last session turns)
    - practice_score: 10% (sessions count, recency, trend)
    """
    cv_score = _compute_cv_score(session, user_id, job_spec_id)
    interview_score = _compute_interview_score(session, user_id, job_spec_id)
    practice_score = _compute_practice_score(session, user_id, job_spec_id)
    
    # Weighted overall
    readiness_score = (cv_score * 0.4 + interview_score * 0.5 + practice_score * 0.1)
    
    breakdown = {
        "cv_score": cv_score,
        "interview_score": interview_score,
        "practice_score": practice_score,
        "weights": {"cv": 0.4, "interview": 0.5, "practice": 0.1}
    }
    
    snapshot = UserReadinessSnapshot(
        user_id=user_id,
        job_spec_id=job_spec_id,
        timestamp=datetime.utcnow(),
        readiness_score=readiness_score,
        cv_score=cv_score,
        interview_score=interview_score,
        practice_score=practice_score,
        breakdown_json=json.dumps(breakdown)
    )
    
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)
    
    return snapshot


def _compute_cv_score(session: Session, user_id: str, job_spec_id: Optional[str]) -> float:
    """Compute CV score (0-100) from cv_analysis_results."""
    if not job_spec_id:
        return 0.0
    
    # Get latest CV analysis result
    latest_analysis = session.exec(
        select(CVAnalysisResult)
        .where(CVAnalysisResult.user_id == user_id)
        .where(CVAnalysisResult.job_spec_id == job_spec_id)
        .order_by(CVAnalysisResult.created_at.desc())
        .limit(1)
    ).first()
    
    if not latest_analysis:
        return 0.0
    
    # Convert match_score (0-1) to 0-100
    base_score = latest_analysis.match_score * 100
    
    # Add coverage heuristics based on strengths/gaps
    strengths = json.loads(latest_analysis.strengths_json or "[]")
    gaps = json.loads(latest_analysis.gaps_json or "[]")
    
    coverage_bonus = min(10.0, len(strengths) * 2.0 - len(gaps) * 1.0)
    
    return max(0.0, min(100.0, base_score + coverage_bonus))


def _compute_interview_score(session: Session, user_id: str, job_spec_id: Optional[str]) -> float:
    """Compute interview score (0-100) from last session turns."""
    # Get latest session
    query = select(InterviewSession).where(InterviewSession.user_id == user_id)
    if job_spec_id:
        query = query.where(InterviewSession.job_spec_id == job_spec_id)
    
    latest_session = session.exec(
        query.order_by(InterviewSession.created_at.desc()).limit(1)
    ).first()
    
    if not latest_session:
        return 0.0
    
    # Get turns from this session
    turns = session.exec(
        select(InterviewTurn)
        .where(InterviewTurn.session_id == latest_session.id)
        .order_by(InterviewTurn.turn_index)
    ).all()
    
    if not turns:
        return 0.0
    
    # Compute average score (weighted: open 0.4, code 0.6)
    scores = []
    weights = []
    
    for turn in turns:
        score_json = json.loads(turn.score_json or "{}")
        overall = float(score_json.get("overall", 0.5))
        
        # Determine question type from session plan or question_id prefix
        question_type = "open"
        if turn.question_id.startswith("code:"):
            question_type = "code"
        
        weight = 0.4 if question_type == "open" else 0.6
        
        scores.append(overall)
        weights.append(weight)
    
    # Weighted average
    if not scores:
        return 0.0
    
    total_weight = sum(weights)
    if total_weight == 0:
        avg_score = sum(scores) / len(scores)
    else:
        avg_score = sum(s * w for s, w in zip(scores, weights)) / total_weight
    
    # Convert 0-1 to 0-100
    return avg_score * 100


def _compute_practice_score(session: Session, user_id: str, job_spec_id: Optional[str]) -> float:
    """Compute practice score (0-100) from sessions count, recency, trend."""
    # Count sessions
    query = select(InterviewSession).where(InterviewSession.user_id == user_id)
    if job_spec_id:
        query = query.where(InterviewSession.job_spec_id == job_spec_id)
    
    all_sessions = list(session.exec(query).all())
    session_count = len(all_sessions)
    
    if session_count == 0:
        return 0.0
    
    # Recency bonus (sessions in last 7 days)
    from datetime import timedelta
    recent_cutoff = datetime.utcnow() - timedelta(days=7)
    recent_count = sum(1 for s in all_sessions if s.created_at >= recent_cutoff)
    
    # Trend (comparing last 2 sessions average scores)
    if session_count >= 2:
        last_two = sorted(all_sessions, key=lambda s: s.created_at, reverse=True)[:2]
        # Simple trend: assume improvement if more recent
        trend_bonus = 5.0
    else:
        trend_bonus = 0.0
    
    # Base score from count
    count_score = min(50.0, session_count * 5.0)
    
    # Recency bonus
    recency_bonus = min(30.0, recent_count * 10.0)
    
    # Total
    return min(100.0, count_score + recency_bonus + trend_bonus)
