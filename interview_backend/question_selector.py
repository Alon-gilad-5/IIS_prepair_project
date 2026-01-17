"""Question selection algorithm with history tracking and diversity."""

import json
import hashlib
import random
from typing import List, Dict, Any, Optional, Set
from sqlmodel import Session, select
from models import QuestionBank, QuestionHistory, QuestionType
from config import MAX_RECENT_SESSIONS, PLAN_SIMILARITY_THRESHOLD


def compute_jaccard_similarity(set1: Set[str], set2: Set[str]) -> float:
    """Compute Jaccard similarity between two sets."""
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0


def compute_match_score(
    question: QuestionBank,
    topic_weights: Dict[str, float]
) -> float:
    """Compute match score for a question based on topic weights."""
    question_topics = json.loads(question.topics or "[]")
    if not question_topics:
        return 0.5  # Default score if no topics
    
    score = 0.0
    for topic in question_topics:
        topic_lower = topic.lower()
        # Try exact match first
        if topic_lower in topic_weights:
            score += topic_weights[topic_lower]
        else:
            # Try partial match
            for weight_topic, weight in topic_weights.items():
                if topic_lower in weight_topic or weight_topic in topic_lower:
                    score += weight * 0.5  # Partial match gets half weight
                    break
    
    return score / max(1, len(question_topics))  # Normalize by topic count


def get_recent_question_ids(
    session: Session,
    user_id: int,
    jd_hash: str,
    limit: int = MAX_RECENT_SESSIONS
) -> Set[int]:
    """Get question IDs from recent sessions for this user+JD."""
    # Get recent session IDs for this user+JD
    from models import InterviewSession, JobSpec
    
    recent_sessions = session.exec(
        select(InterviewSession.id)
        .join(JobSpec)
        .where(
            InterviewSession.user_id == user_id,
            JobSpec.jd_hash == jd_hash
        )
        .order_by(InterviewSession.started_at.desc())
        .limit(limit)
    ).all()
    
    if not recent_sessions:
        return set()
    
    # Get question IDs from those sessions
    from models import InterviewTurn
    
    question_ids = session.exec(
        select(InterviewTurn.question_id)
        .where(InterviewTurn.session_id.in_(recent_sessions))
        .where(InterviewTurn.question_id.isnot(None))
    ).all()
    
    return set(qid for qid in question_ids if qid is not None)


def select_questions(
    session: Session,
    topic_weights: Dict[str, float],
    question_type: QuestionType,
    num_questions: int,
    user_id: int,
    jd_hash: str,
    exclude_question_ids: Optional[Set[int]] = None,
    difficulty_filter: Optional[str] = None
) -> List[QuestionBank]:
    """Select questions using weighted sampling with constraints."""
    
    # Get candidate questions
    query = select(QuestionBank).where(QuestionBank.question_type == question_type)
    
    if difficulty_filter:
        query = query.where(QuestionBank.difficulty == difficulty_filter)
    
    candidates = list(session.exec(query).all())
    
    if not candidates:
        return []
    
    # Get recent question IDs to exclude
    recent_ids = get_recent_question_ids(session, user_id, jd_hash)
    if exclude_question_ids:
        recent_ids.update(exclude_question_ids)
    
    # Filter out recently asked questions
    filtered_candidates = [
        q for q in candidates
        if q.id not in recent_ids
    ]
    
    if not filtered_candidates:
        # Fallback: use all candidates if no filtered ones
        filtered_candidates = candidates
    
    # Compute match scores
    scored_questions = [
        (q, compute_match_score(q, topic_weights))
        for q in filtered_candidates
    ]
    
    # Sort by score (descending)
    scored_questions.sort(key=lambda x: x[1], reverse=True)
    
    # Weighted sampling: take top candidates but add some randomness
    selected = []
    used_ids = set()
    
    # Take top N with some diversity
    top_k = min(num_questions * 3, len(scored_questions))
    top_candidates = scored_questions[:top_k]
    
    # Select with diversity check
    while len(selected) < num_questions and top_candidates:
        # First, try to select from high-scoring questions
        remaining = [sq for sq in top_candidates if sq[0].id not in used_ids]
        
        if not remaining:
            break
        
        # Weighted random selection from remaining (favor higher scores)
        weights = [sq[1] ** 2 for sq in remaining]  # Square to emphasize differences
        chosen = random.choices(remaining, weights=weights, k=1)[0]
        
        selected.append(chosen[0])
        used_ids.add(chosen[0].id)
        
        # Remove questions with high topic overlap (optional diversity filter)
        if len(selected) > 1:
            selected_topics = set()
            for prev_q in selected[:-1]:
                selected_topics.update(json.loads(prev_q.topics or "[]"))
            
            new_topics = set(json.loads(chosen[0].topics or "[]"))
            overlap = compute_jaccard_similarity(selected_topics, new_topics)
            
            # If overlap is too high, remove and try next
            if overlap > 0.8 and len(remaining) > 1:
                selected.pop()
                used_ids.remove(chosen[0].id)
                top_candidates.remove(chosen)
                continue
    
    return selected[:num_questions]


def build_interview_plan(
    session: Session,
    role_profile: Dict[str, Any],
    user_id: int,
    jd_hash: str,
    num_open: int = 5,
    num_code: int = 3,
    duration_minutes: int = 30
) -> List[Dict[str, Any]]:
    """Build an interview plan with questions."""
    
    # Normalize topic weights
    topics_list = role_profile.get("topics", [])
    topic_weights = {}
    for item in topics_list:
        if isinstance(item, dict):
            name = item.get("name", "").lower()
            weight = float(item.get("weight", 0.5))
            topic_weights[name] = weight
        elif isinstance(item, str):
            topic_weights[item.lower()] = 0.6  # Default weight
    
    # If no topics, use defaults
    if not topic_weights:
        topic_weights = {
            "programming": 0.8,
            "problem solving": 0.7,
            "algorithms": 0.6
        }
    
    plan_items = []
    
    # Section 1: Open questions
    open_questions = select_questions(
        session, topic_weights, QuestionType.OPEN,
        num_open, user_id, jd_hash
    )
    
    for idx, q in enumerate(open_questions):
        plan_items.append({
            "section": "open",
            "slot_index": idx,
            "question_id": q.id,
            "question_text": q.question_text,
            "question_type": "open",
            "topics": json.loads(q.topics or "[]"),
            "candidates": []  # For adaptive slots, store 2-3 candidates
        })
    
    # Section 2: Code questions (with adaptive candidates)
    # For each code slot, select 2-3 candidates of varying difficulty
    code_slots = []
    difficulties = ["Easy", "Medium", "Hard"]
    
    for slot_idx in range(num_code):
        candidates = []
        
        # Try to get one question per difficulty (if available)
        for difficulty in difficulties:
            qs = select_questions(
                session, topic_weights, QuestionType.CODE,
                1, user_id, jd_hash,
                difficulty_filter=difficulty
            )
            if qs:
                candidates.append({
                    "question_id": qs[0].id,
                    "question_text": qs[0].question_text,
                    "difficulty": qs[0].difficulty or "Medium",
                    "topics": json.loads(qs[0].topics or "[]"),
                })
        
        # If no candidates, try without difficulty filter
        if not candidates:
            qs = select_questions(
                session, topic_weights, QuestionType.CODE,
                1, user_id, jd_hash
            )
            if qs:
                candidates.append({
                    "question_id": qs[0].id,
                    "question_text": qs[0].question_text,
                    "difficulty": qs[0].difficulty or "Medium",
                    "topics": json.loads(qs[0].topics or "[]"),
                })
        
        if candidates:
            # Select first candidate as primary
            primary = candidates[0]
            plan_items.append({
                "section": "code",
                "slot_index": slot_idx,
                "question_id": primary["question_id"],
                "question_text": primary["question_text"],
                "question_type": "code",
                "difficulty": primary["difficulty"],
                "topics": primary["topics"],
                "candidates": candidates  # Store alternatives for adaptive selection
            })
    
    return plan_items


def check_plan_diversity(
    session: Session,
    user_id: int,
    jd_hash: str,
    new_plan: List[Dict[str, Any]]
) -> bool:
    """Check if new plan is sufficiently different from previous plans."""
    from models import InterviewSession, JobSpec
    
    # Get previous plan for this user+JD
    prev_session = session.exec(
        select(InterviewSession)
        .join(JobSpec)
        .where(
            InterviewSession.user_id == user_id,
            JobSpec.jd_hash == jd_hash
        )
        .order_by(InterviewSession.started_at.desc())
        .limit(1)
    ).first()
    
    if not prev_session or not prev_session.plan:
        return True  # No previous plan, so diversity is fine
    
    try:
        prev_plan = json.loads(prev_session.plan)
        prev_q_ids = {item.get("question_id") for item in prev_plan if item.get("question_id")}
        new_q_ids = {item.get("question_id") for item in new_plan if item.get("question_id")}
        
        similarity = compute_jaccard_similarity(prev_q_ids, new_q_ids)
        return similarity < PLAN_SIMILARITY_THRESHOLD
    except:
        return True  # If parsing fails, assume diverse
