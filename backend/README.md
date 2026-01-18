# PrepAIr Backend

FastAPI + SQLite backend providing REST API for CV analysis, interview sessions, and progress tracking.

## 🏗️ Architecture

- **Framework:** FastAPI with async support
- **Database:** SQLite with SQLModel ORM
- **LLM:** Google Gemini 2.5 Pro
- **Validation:** Pydantic schemas

## 📁 Structure

```
backend/
├── main.py              # FastAPI app entry point
├── db.py                # Database setup & session management
├── models.py            # SQLModel database models (10 models)
├── schemas.py           # Pydantic request/response schemas
├── requirements.txt     # Python dependencies
├── services/            # Business logic
│   ├── ingest.py           # CSV data ingestion
│   ├── gemini_client.py    # Gemini API client wrapper
│   ├── role_profile.py     # Role profile extraction from CV+JD
│   ├── selection.py        # Question selection & plan building
│   ├── scoring.py          # Answer scoring & follow-up generation
│   └── readiness.py        # Readiness score calculation
└── routers/             # API route handlers
    ├── users.py            # User management
    ├── cv.py               # CV operations (ingest, analyze, save)
    ├── jd.py               # Job description management
    ├── interview.py        # Interview session management
    └── progress.py         # Progress & readiness tracking
```

## 🚀 Setup

### Prerequisites

- Python 3.8+
- Google Gemini API Key

### Installation

```bash
# From project root
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

pip install -r backend/requirements.txt
```

### Configuration

Set environment variables:

```bash
GEMINI_API_KEY=your_api_key_here
DATA_DIR=src/data/questions_and_answers  # Relative to project root
DB_PATH=backend/data/app.db
```

Or use `api_keys.json` in project root.

### Database Initialization

Database is auto-created on first startup. Tables are created via SQLModel.

```bash
# Manual initialization (optional)
python -c "from backend.db import init_db; init_db()"
```

### Data Ingestion

Load questions from CSV files:

```bash
python -m backend.services.ingest
```

This loads:
- `all_code_questions_with_topics.csv` → code questions
- `all_open_questions_with_topics.csv` → behavioral questions
- Optionally merges solutions from `all_code_problems_with_solutions.csv`

### Running

```bash
uvicorn backend.main:app --reload --port 8000
```

Backend available at `http://localhost:8000`

## 🗄️ Database Models

10 core models:

1. **User** - User accounts (UUID-based)
2. **CVVersion** - CV text versions with parent-child relationships
3. **CVAnalysisResult** - CV analysis results (match scores, strengths, gaps)
4. **JobSpec** - Job descriptions with extracted role profiles
5. **QuestionBank** - Ingested questions from CSV
6. **InterviewSession** - Interview session records
7. **InterviewTurn** - Individual Q&A turns
8. **QuestionHistory** - Track asked questions per user+JD
9. **UserSkillState** - User skill mastery tracking
10. **UserReadinessSnapshot** - Readiness score snapshots

See `models.py` for full schema.

## 📡 API Endpoints

See [docs/api.yaml](../docs/api.yaml) for complete OpenAPI specification.

**Key Endpoints:**

- `POST /api/users/ensure` - Ensure user exists
- `POST /api/cv/ingest` - Ingest CV text
- `POST /api/cv/analyze` - Analyze CV against job spec
- `POST /api/jd/ingest` - Ingest job description
- `POST /api/interview/start` - Start interview session
- `POST /api/interview/next` - Process answer, get next question
- `POST /api/interview/end` - End interview session
- `GET /api/progress/overview` - Get readiness progress

## 🔧 Key Services

### Role Profile Extraction (`role_profile.py`)
- Extracts role profile from CV + JD using Gemini
- Outputs: role_title, seniority, must_have_topics, weights, etc.
- Fallback keyword extraction if Gemini unavailable

### Question Selection (`selection.py`)
- Weighted sampling based on topic intersection with role profile
- Diversity constraints (Jaccard similarity)
- Excludes recently asked questions
- Adaptive candidates for code questions (Easy/Medium/Hard)

### Scoring (`scoring.py`)
- Gemini-powered rubric scoring (clarity, relevance, structure, correctness, depth)
- For code questions: scores reasoning/approach, NOT code execution
- Fallback heuristics if Gemini unavailable
- Follow-up question generation for low scores

### Readiness Calculation (`readiness.py`)
- Weighted formula: CV Score (40%) + Interview Score (50%) + Practice Score (10%)
- Snapshots created after CV analysis and interview end
- Enables trend tracking over time

## 🛠️ Development

### Adding New Endpoints

1. Create schema in `schemas.py`
2. Add route handler in `routers/`
3. Register router in `main.py`
4. Update `docs/api.yaml`

### Database Migrations

SQLite with auto-creation. For production, consider:
- Alembic for migrations
- PostgreSQL instead of SQLite

### Testing

```bash
# Health check
curl http://localhost:8000/api/health

# Interactive docs
http://localhost:8000/docs
```

## 🔍 Troubleshooting

**Database errors:**
- Ensure `backend/data/` directory exists
- Check `DB_PATH` environment variable

**API key errors:**
- Verify `GEMINI_API_KEY` in `.env` or `api_keys.json`
- System uses fallbacks if key unavailable (heuristics)

**Question bank empty:**
- Run: `python -m backend.services.ingest`
- Check CSV files exist in `DATA_DIR`

## 📝 Notes

- All JSON fields stored as strings (SQLite limitation)
- UUID strings for user-facing IDs
- Safe fallbacks throughout (system works without Gemini API key)
- CORS configured for `localhost:5173` (frontend)
