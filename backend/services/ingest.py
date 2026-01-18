"""Data ingestion service for loading questions from CSV files."""

import csv
import json
import hashlib
import os
from pathlib import Path
from sqlmodel import Session, select
from backend.models import QuestionBank, QuestionType
from backend.db import init_db, engine


def get_data_dir() -> Path:
    """Get data directory path from env or default location."""
    data_dir = os.getenv("DATA_DIR")
    if data_dir:
        return Path(data_dir)
    
    # Try default locations
    defaults = [
        Path("src/data/questions_and_answers"),
        Path("backend/data_sources"),
        Path(__file__).parent.parent.parent / "src" / "data" / "questions_and_answers"
    ]
    
    for default in defaults:
        if default.exists():
            return default
    
    # Return first default as fallback
    return defaults[0]


def normalize_topics(topics_str: str) -> list:
    """Normalize topics string to JSON array of strings."""
    if not topics_str or topics_str.strip() == "":
        return []
    
    # Try JSON first
    try:
        parsed = json.loads(topics_str)
        if isinstance(parsed, list):
            return [str(t).strip() for t in parsed if t]
        elif isinstance(parsed, str):
            return [parsed.strip()]
    except:
        pass
    
    # Try comma-separated
    if "," in topics_str:
        topics = [t.strip() for t in topics_str.split(",") if t.strip()]
        return topics
    
    # Single topic
    return [topics_str.strip()] if topics_str.strip() else []


def generate_question_id(question_type: str, row: dict, index: int) -> str:
    """Generate question ID: code:<id> or open:<id>."""
    # Try to use existing question_id if available
    if "question_id" in row and row["question_id"]:
        base_id = str(row["question_id"]).strip()
        return f"{question_type}:{base_id}"
    
    # Fallback: hash the question text
    question_text = row.get("question", "") or row.get("formatted_title", "") or row.get("title", "")
    if question_text:
        hash_obj = hashlib.md5(question_text.encode())
        return f"{question_type}:{hash_obj.hexdigest()[:12]}"
    
    # Last resort
    return f"{question_type}:gen_{index}"


def ingest_open_questions_with_topics(session: Session, file_path: Path) -> int:
    """Ingest open questions with topics CSV."""
    if not file_path.exists():
        print(f"⚠️  File not found: {file_path}")
        return 0
    
    print(f"📖 Loading {file_path.name}...")
    count = 0
    
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            question_id = generate_question_id("open", row, idx)
            
            # Check if already exists (upsert by id)
            existing = session.get(QuestionBank, question_id)
            
            question_text = row.get("question", "").strip()
            if not question_text:
                continue
            
            topics = normalize_topics(row.get("topics", ""))
            category = row.get("category", None)
            
            if existing:
                # Update existing
                existing.question_text = question_text
                existing.topics_json = json.dumps(topics)
                existing.category = category
            else:
                # Create new
                qb = QuestionBank(
                    id=question_id,
                    question_type=QuestionType.OPEN,
                    question_text=question_text,
                    topics_json=json.dumps(topics),
                    category=category,
                    source="csv"
                )
                session.add(qb)
            
            count += 1
            
            # Commit in batches
            if count % 100 == 0:
                session.commit()
    
    session.commit()
    print(f"  ✅ Processed {count} open questions with topics")
    return count


def ingest_code_questions_with_topics(session: Session, file_path: Path) -> int:
    """Ingest code questions with topics CSV."""
    if not file_path.exists():
        print(f"⚠️  File not found: {file_path}")
        return 0
    
    print(f"📖 Loading {file_path.name}...")
    count = 0
    
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            question_id = generate_question_id("code", row, idx)
            
            # Check if already exists
            existing = session.get(QuestionBank, question_id)
            
            question_text = (row.get("question", "") or row.get("formatted_title", "") or "").strip()
            if not question_text:
                continue
            
            topics = normalize_topics(row.get("topics", ""))
            difficulty = row.get("difficulty", "").strip().capitalize() if row.get("difficulty") else None
            category = row.get("category", None)
            
            if existing:
                # Update existing
                existing.question_text = question_text
                existing.topics_json = json.dumps(topics)
                existing.difficulty = difficulty
                existing.category = category
            else:
                # Create new
                qb = QuestionBank(
                    id=question_id,
                    question_type=QuestionType.CODE,
                    question_text=question_text,
                    topics_json=json.dumps(topics),
                    difficulty=difficulty,
                    category=category,
                    source="csv"
                )
                session.add(qb)
            
            count += 1
            
            # Commit in batches
            if count % 100 == 0:
                session.commit()
    
    session.commit()
    print(f"  ✅ Processed {count} code questions with topics")
    return count


def merge_solutions(session: Session, solutions_file: Path) -> int:
    """Merge solution_text from all_code_problems_with_solutions.csv by question_id."""
    if not solutions_file.exists():
        print(f"⚠️  Solutions file not found: {solutions_file}")
        return 0
    
    print(f"📖 Merging solutions from {solutions_file.name}...")
    count = 0
    
    # Build mapping of question_id -> solution_text
    solutions_map = {}
    
    with open(solutions_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            question_id_val = row.get("question_id", "").strip()
            solution_text = row.get("solution_text", "").strip()
            
            if question_id_val and solution_text:
                # Try code:question_id format
                solutions_map[f"code:{question_id_val}"] = solution_text
    
    # Update questions with solutions
    for question_id, solution_text in solutions_map.items():
        question = session.get(QuestionBank, question_id)
        if question and not question.solution_text:
            question.solution_text = solution_text
            count += 1
    
    session.commit()
    print(f"  ✅ Merged {count} solutions")
    return count


def main():
    """Main ingestion function."""
    print("🚀 Starting data ingestion...")
    
    # Initialize database
    init_db()
    
    data_dir = get_data_dir()
    
    # CSV file paths
    csv_paths = {
        "open_with_topics": data_dir / "all_open_questions_with_topics.csv",
        "code_with_topics": data_dir / "all_code_questions_with_topics.csv",
        "code_solutions": data_dir / "all_code_problems_with_solutions.csv",
    }
    
    with Session(engine) as session:
        total = 0
        
        # Ingest code questions (primary source)
        total += ingest_code_questions_with_topics(session, csv_paths["code_with_topics"])
        
        # Ingest open questions (primary source)
        total += ingest_open_questions_with_topics(session, csv_paths["open_with_topics"])
        
        # Merge solutions if available
        merge_solutions(session, csv_paths["code_solutions"])
        
        print(f"\n✅ Ingestion complete! Total questions: {total}")


if __name__ == "__main__":
    main()
