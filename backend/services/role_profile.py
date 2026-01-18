"""Role profile extraction from CV and JD using Gemini."""

import json
from typing import Dict, Any, Optional
from backend.services.gemini_client import call_gemini


def extract_role_profile(cv_text: str, jd_text: str) -> Dict[str, Any]:
    """
    Extract role profile from CV and JD with strict JSON parsing.
    
    Returns:
        {
            "role_title": str,
            "seniority": "intern"|"junior"|"mid"|"senior",
            "must_have_topics": List[str],
            "nice_to_have_topics": List[str],
            "soft_skills": List[str],
            "coding_focus": List[str],
            "weights": Dict[str, float]  # topic -> 0-1
        }
    """
    system_prompt = """You are an expert at analyzing job descriptions and CVs to extract role profiles.
Extract structured information about the role, required skills, and importance weights.
Always respond with valid JSON only."""
    
    user_prompt = f"""Analyze the CV and Job Description below:

CV Text:
{cv_text[:3000]}

Job Description:
{jd_text[:3000]}

Extract and return a JSON object with this exact structure:
{{
    "role_title": "Software Engineer",
    "seniority": "mid",
    "must_have_topics": ["Python", "REST APIs", "Docker"],
    "nice_to_have_topics": ["Kubernetes", "AWS"],
    "soft_skills": ["Communication", "Teamwork"],
    "coding_focus": ["Backend Development", "API Design"],
    "weights": {{
        "Python": 0.9,
        "REST APIs": 0.8,
        "Docker": 0.7
    }}
}}

Rules:
- seniority must be one of: "intern", "junior", "mid", "senior"
- weights should be floats between 0.0 and 1.0
- must_have_topics and nice_to_have_topics should be lists of strings
- Extract at least 5-10 must_have topics and their weights
- Return ONLY valid JSON, no markdown or code blocks"""
    
    try:
        response_text = call_gemini(system_prompt, user_prompt)
        
        # Clean response (remove markdown if present)
        response_text = response_text.strip()
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        # Parse JSON
        result = json.loads(response_text)
        
        # Validate structure
        result = {
            "role_title": result.get("role_title", "Software Developer"),
            "seniority": _normalize_seniority(result.get("seniority", "mid")),
            "must_have_topics": list(result.get("must_have_topics", []))[:15],
            "nice_to_have_topics": list(result.get("nice_to_have_topics", []))[:10],
            "soft_skills": list(result.get("soft_skills", []))[:10],
            "coding_focus": list(result.get("coding_focus", []))[:10],
            "weights": _normalize_weights(result.get("weights", {}))
        }
        
        return result
        
    except Exception as e:
        print(f"⚠️  Role profile extraction failed: {e}. Using fallback.")
        # Fallback: keyword-based extraction
        return _fallback_role_profile(jd_text)


def _normalize_seniority(seniority: str) -> str:
    """Normalize seniority to valid values."""
    seniority_lower = str(seniority).lower()
    valid = ["intern", "junior", "mid", "senior"]
    for v in valid:
        if v in seniority_lower:
            return v
    return "mid"


def _normalize_weights(weights: Dict[str, Any]) -> Dict[str, float]:
    """Normalize weights to floats 0-1."""
    normalized = {}
    for topic, weight in weights.items():
        try:
            w = float(weight)
            normalized[str(topic)] = max(0.0, min(1.0, w))
        except (ValueError, TypeError):
            continue
    return normalized


def _fallback_role_profile(jd_text: str) -> Dict[str, Any]:
    """Fallback keyword extraction from JD."""
    jd_lower = jd_text.lower()
    
    # Simple keyword matching
    common_tech = ["python", "javascript", "java", "react", "docker", "aws", "sql", "rest"]
    found_topics = [tech for tech in common_tech if tech in jd_lower]
    
    # Default weights
    weights = {topic: 0.7 for topic in found_topics[:10]}
    if not weights:
        weights = {"Programming": 0.7}
    
    return {
        "role_title": "Software Developer",
        "seniority": "mid",
        "must_have_topics": list(weights.keys())[:10],
        "nice_to_have_topics": [],
        "soft_skills": [],
        "coding_focus": [],
        "weights": weights
    }
