"""Gemini API helpers for role extraction, scoring, and follow-up generation."""

import json
from typing import Dict, Optional, Any
from src.shared.gemini_client import call_gemini_json


def extract_role_profile(cv_text: str, jd_text: str) -> Dict[str, Any]:
    """
    Extract role profile (topics, weights, seniority) from CV and JD.
    
    Returns:
        {
            "topics": [{"name": str, "weight": float}],
            "seniority": "junior" | "mid" | "senior" | "lead",
            "focus_areas": [str]
        }
    """
    prompt = f"""Analyze the CV and Job Description to extract a structured role profile.

CV Text:
{cv_text[:2000]}

Job Description:
{jd_text[:2000]}

Extract:
1. Technical topics/skills relevant to the role (with importance weights 0.0-1.0)
2. Seniority level (junior, mid, senior, lead)
3. Key focus areas

Return ONLY valid JSON in this exact format:
{{
    "topics": [
        {{"name": "Python", "weight": 0.9}},
        {{"name": "Machine Learning", "weight": 0.8}},
        {{"name": "Data Structures", "weight": 0.7}}
    ],
    "seniority": "mid",
    "focus_areas": ["Backend Development", "API Design"]
}}

Keep topics list to 10-15 most important items. Seniority should be one of: junior, mid, senior, lead."""

    try:
        result = call_gemini_json(prompt, max_retries=2)
        
        # Validate structure
        if not isinstance(result, dict):
            raise ValueError("Response is not a dictionary")
        
        # Ensure topics is a list
        if "topics" not in result or not isinstance(result["topics"], list):
            result["topics"] = []
        
        # Normalize seniority
        seniority = result.get("seniority", "mid").lower()
        if seniority not in ["junior", "mid", "senior", "lead"]:
            seniority = "mid"
        result["seniority"] = seniority
        
        return result
        
    except Exception as e:
        print(f"⚠️  Gemini role extraction failed: {e}. Using fallback.")
        # Fallback: simple keyword-based extraction
        return {
            "topics": [
                {"name": "General Programming", "weight": 0.7},
                {"name": "Problem Solving", "weight": 0.6}
            ],
            "seniority": "mid",
            "focus_areas": ["Technical Skills"]
        }


def score_answer(
    question: str,
    transcript: str,
    reference_solution: Optional[str],
    topics: list
) -> Dict[str, Any]:
    """
    Score an answer using Gemini.
    
    Returns:
        {
            "overall_score": float (0-100),
            "strengths": [str],
            "weaknesses": [str],
            "topic_scores": {topic: float},
            "feedback": str
        }
    """
    is_code = reference_solution is not None
    
    prompt = f"""Evaluate the following interview answer.

Question: {question}

Answer (transcript): {transcript}

Relevant Topics: {', '.join(topics[:10])}

{"Reference Solution: " + reference_solution[:1000] if reference_solution else ""}

Provide a score (0-100) and feedback.

Return ONLY valid JSON:
{{
    "overall_score": 75,
    "strengths": ["Clear explanation", "Good examples"],
    "weaknesses": ["Missing edge cases"],
    "topic_scores": {{"Python": 80, "Algorithms": 70}},
    "feedback": "Good overall understanding, but could improve..."
}}"""

    try:
        result = call_gemini_json(prompt, max_retries=2)
        
        # Validate and normalize
        score = result.get("overall_score", 50)
        if not isinstance(score, (int, float)):
            score = 50
        score = max(0, min(100, float(score)))
        
        return {
            "overall_score": score,
            "strengths": result.get("strengths", []) or [],
            "weaknesses": result.get("weaknesses", []) or [],
            "topic_scores": result.get("topic_scores", {}) or {},
            "feedback": result.get("feedback", ""),
        }
        
    except Exception as e:
        print(f"⚠️  Gemini scoring failed: {e}. Using fallback.")
        # Fallback: simple heuristic
        transcript_length = len(transcript.split())
        score = min(100, max(40, transcript_length * 2))
        
        return {
            "overall_score": score,
            "strengths": ["Answer provided"],
            "weaknesses": [],
            "topic_scores": {},
            "feedback": "Unable to provide detailed feedback.",
        }


def maybe_generate_followup(
    question: str,
    transcript: str,
    score_json: Dict[str, Any]
) -> Optional[str]:
    """
    Generate a follow-up question if appropriate.
    Returns None if no follow-up needed.
    """
    # Only generate follow-up for lower scores or if answer is too short
    score = score_json.get("overall_score", 50)
    if score >= 70 or len(transcript.split()) > 100:
        return None
    
    prompt = f"""Based on this interview exchange, generate a brief, helpful follow-up question (one sentence).

Original Question: {question}
Answer: {transcript}
Score: {score}/100
Weaknesses: {', '.join(score_json.get('weaknesses', [])[:3])}

Generate a single, concise follow-up question that helps clarify or deepen the response. 
If no follow-up is needed, return null.

Return ONLY valid JSON:
{{
    "followup": "Can you provide a specific example of when you used this approach?"
}}

Or:
{{
    "followup": null
}}"""

    try:
        result = call_gemini_json(prompt, max_retries=1)
        followup = result.get("followup")
        if followup and isinstance(followup, str) and len(followup.strip()) > 0:
            return followup.strip()
        return None
        
    except Exception as e:
        print(f"⚠️  Follow-up generation failed: {e}")
        return None
