"""Configuration for PrepAIr backend."""

import os
from pathlib import Path
from src.shared.gemini_client import get_gemini_api_key

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./interview_simulator.db")

# Gemini API
try:
    GEMINI_API_KEY = get_gemini_api_key()
except ValueError as e:
    raise ValueError(f"Failed to get GEMINI_API_KEY: {str(e)}")

# Data paths (support both /mnt/data for Replit and local paths)
DATA_DIR = Path(os.getenv("DATA_DIR", "src/data/questions_and_answers"))
if not DATA_DIR.exists():
    # Try alternative path
    DATA_DIR = Path("src/data/questions_and_answers")

# Question bank CSVs
CSV_PATHS = {
    "open_with_topics": DATA_DIR / "all_open_questions_with_topics.csv",
    "open": DATA_DIR / "all_open_questions.csv",
    "code_with_topics": DATA_DIR / "all_code_questions_with_topics.csv",
    "code_problems": DATA_DIR / "leetcode_problems_data.csv",
    "code_problems_with_solutions": DATA_DIR / "all_code_problems_with_solutions.csv",  # If available
}

# Default interview settings
DEFAULT_NUM_OPEN = 5
DEFAULT_NUM_CODE = 3
DEFAULT_DURATION_MINUTES = 30
MAX_RECENT_SESSIONS = 3  # Don't repeat questions from last N sessions

# Jaccard similarity threshold for plan diversity
PLAN_SIMILARITY_THRESHOLD = 0.7
