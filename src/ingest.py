"""Data ingestion script for loading questions from CSV files into database."""

import csv
import json
import hashlib
from pathlib import Path
from sqlmodel import Session, select
from src.database import engine, init_db
from src.models.database import QuestionBank, QuestionType
from src.config import CSV_PATHS


def normalize_topics(topics_str: str) -> list:
    """Normalize topics string to a list of topic strings."""
    if not topics_str or topics_str.strip() == "":
        return []
    
    # Try parsing as JSON first
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
    """Generate unique question ID."""
    # Try to use existing question_id if available
    if "question_id" in row and row["question_id"]:
        return f"{question_type}_{row['question_id']}"
    
    # Fallback: hash the question text
    question_text = row.get("question", "") or row.get("formatted_title", "") or row.get("title", "")
    if question_text:
        hash_obj = hashlib.md5(question_text.encode())
        return f"{question_type}_{hash_obj.hexdigest()[:12]}"
    
    # Last resort
    return f"{question_type}_gen_{index}"


def ingest_open_questions_with_topics(session: Session, file_path: Path):
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
            
            # Check if already exists
            existing = session.exec(
                select(QuestionBank).where(QuestionBank.question_id == question_id)
            ).first()
            
            if existing:
                continue  # Skip if already ingested
            
            question_text = row.get("question", "").strip()
            if not question_text:
                continue
            
            topics = normalize_topics(row.get("topics", ""))
            
            qb = QuestionBank(
                question_id=question_id,
                question_type=QuestionType.OPEN,
                question_text=question_text,
                topics=json.dumps(topics),
                category=row.get("category", None),
            )
            session.add(qb)
            count += 1
    
    session.commit()
    print(f"  ✅ Loaded {count} open questions with topics")
    return count


def ingest_open_questions(session: Session, file_path: Path):
    """Ingest open questions CSV (without detailed topics)."""
    if not file_path.exists():
        print(f"⚠️  File not found: {file_path}")
        return 0
    
    print(f"📖 Loading {file_path.name}...")
    count = 0
    
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            question_id = generate_question_id("open", row, idx)
            
            # Check if already exists
            existing = session.exec(
                select(QuestionBank).where(QuestionBank.question_id == question_id)
            ).first()
            
            if existing:
                continue
            
            question_text = row.get("question", "").strip()
            if not question_text:
                continue
            
            topics = normalize_topics(row.get("topics", "") or row.get("category", ""))
            
            qb = QuestionBank(
                question_id=question_id,
                question_type=QuestionType.OPEN,
                question_text=question_text,
                topics=json.dumps(topics),
                category=row.get("category", None),
            )
            session.add(qb)
            count += 1
    
    session.commit()
    print(f"  ✅ Loaded {count} open questions")
    return count


def ingest_code_questions_with_topics(session: Session, file_path: Path):
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
            existing = session.exec(
                select(QuestionBank).where(QuestionBank.question_id == question_id)
            ).first()
            
            if existing:
                continue
            
            question_text = (row.get("question", "") or row.get("formatted_title", "") or "").strip()
            if not question_text:
                continue
            
            topics = normalize_topics(row.get("topics", ""))
            difficulty = row.get("difficulty", "").strip().capitalize() if row.get("difficulty") else None
            solution = row.get("solution", "").strip() if row.get("solution") else None
            solution_url = row.get("solution_URL", "").strip() if row.get("solution_URL") else None
            
            metadata = {}
            if row.get("acceptance"):
                metadata["acceptance"] = row.get("acceptance")
            if row.get("similar_questions"):
                metadata["similar_questions"] = row.get("similar_questions")
            
            qb = QuestionBank(
                question_id=question_id,
                question_type=QuestionType.CODE,
                question_text=question_text,
                topics=json.dumps(topics),
                difficulty=difficulty,
                solution=solution,
                solution_url=solution_url,
                metadata=json.dumps(metadata) if metadata else None,
            )
            session.add(qb)
            count += 1
    
    session.commit()
    print(f"  ✅ Loaded {count} code questions with topics")
    return count


def ingest_code_problems(session: Session, file_path: Path):
    """Ingest LeetCode problems data CSV."""
    if not file_path.exists():
        print(f"⚠️  File not found: {file_path}")
        return 0
    
    print(f"📖 Loading {file_path.name}...")
    count = 0
    
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            question_id_val = row.get("question_id", "").strip()
            if not question_id_val:
                continue
            
            question_id = f"code_leetcode_{question_id_val}"
            
            # Check if already exists
            existing = session.exec(
                select(QuestionBank).where(QuestionBank.question_id == question_id)
            ).first()
            
            if existing:
                continue
            
            question_text = (row.get("content", "") or row.get("title", "") or "").strip()
            if not question_text:
                continue
            
            # Try to infer topics from title/slug
            slug = row.get("slug", "")
            title = row.get("title", "")
            topics = []
            
            difficulty = row.get("difficulty", "").strip().capitalize() if row.get("difficulty") else None
            
            metadata = {}
            if row.get("likes"):
                metadata["likes"] = row.get("likes")
            if row.get("dislikes"):
                metadata["dislikes"] = row.get("dislikes")
            if slug:
                metadata["slug"] = slug
            
            qb = QuestionBank(
                question_id=question_id,
                question_type=QuestionType.CODE,
                question_text=question_text,
                topics=json.dumps(topics),
                difficulty=difficulty,
                metadata=json.dumps(metadata) if metadata else None,
            )
            session.add(qb)
            count += 1
    
    session.commit()
    print(f"  ✅ Loaded {count} code problems")
    return count


def main():
    """Main ingestion function."""
    print("🚀 Starting data ingestion...")
    
    # Initialize database
    init_db()
    
    with Session(engine) as session:
        total = 0
        
        # Priority order: most detailed first
        total += ingest_open_questions_with_topics(session, CSV_PATHS["open_with_topics"])
        total += ingest_code_questions_with_topics(session, CSV_PATHS["code_with_topics"])
        
        # Fallback sources (only if primary ones didn't have enough)
        if total < 100:
            total += ingest_open_questions(session, CSV_PATHS["open"])
            total += ingest_code_problems(session, CSV_PATHS["code_problems"])
        
        print(f"\n✅ Ingestion complete! Total questions loaded: {total}")


if __name__ == "__main__":
    main()
