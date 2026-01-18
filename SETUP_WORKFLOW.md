# PrepAIr Setup Workflow

This document provides step-by-step instructions to set up and run the PrepAIr application.

## Prerequisites

- Python 3.8+
- Node.js 18+
- Google Gemini API Key ([Get one here](https://makersuite.google.com/app/apikey))

## Step 1: Clone and Navigate

```bash
git clone <repo-url>
cd IIS_prepair_project
```

## Step 2: Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

## Step 3: Install Backend Dependencies

```bash
pip install -r backend/requirements.txt
```

This installs:
- FastAPI and Uvicorn (web server)
- SQLModel (database ORM)
- Google Generative AI (Gemini API client)
- Pydantic (data validation)
- Python-dotenv (environment variables)

## Step 4: Configure Environment Variables

Create a `.env` file in the root directory:

```bash
GEMINI_API_KEY=your_api_key_here
DATA_DIR=src/data/questions_and_answers
DB_PATH=backend/data/app.db
```

Alternatively, add to `api_keys.json`:

```json
{
    "GEMINI_API_KEY": "your_api_key_here"
}
```

## Step 5: Ingest Question Data

Run the ingestion script to load questions into the database:

```bash
python -m backend.services.ingest
```

This will:
- Load code questions from `all_code_questions_with_topics.csv`
- Load open questions from `all_open_questions_with_topics.csv`
- Optionally merge solutions from `all_code_problems_with_solutions.csv`

**Note:** If the question bank is empty when you start the backend, it will warn you to run this command manually.

## Step 6: Start Backend Server

In your terminal (with venv activated):

```bash
uvicorn backend.main:app --reload --port 8000
```

The backend API will be available at `http://localhost:8000`

You should see:
- `🚀 Starting PrepAIr backend...`
- `✅ Database initialized`
- `📚 Question bank has X questions`

## Step 7: Set Up Frontend (New Terminal)

Open a **new terminal** and navigate to the app directory:

```bash
cd app
npm install
```

This installs React, React Router, TypeScript, and Vite dependencies.

## Step 8: Start Frontend Development Server

```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

Vite will automatically proxy API requests from `/api/*` to `http://localhost:8000`.

## Step 9: Open Application

Navigate to `http://localhost:5173` in your browser.

You should see the **Landing** page with options to:
- Start Interview Now
- Improve CV First
- Dashboard

## Verification Checklist

- [ ] Backend is running on port 8000
- [ ] Frontend is running on port 5173
- [ ] Question bank has been ingested (check backend logs)
- [ ] GEMINI_API_KEY is set (backend won't crash without it, but will use fallbacks)
- [ ] Database file exists at `backend/data/app.db` (auto-created on first run)

## Troubleshooting

### Backend Issues

**Database errors:**
- Ensure `backend/data/` directory exists: `mkdir -p backend/data`

**API key errors:**
- Check `.env` file or `api_keys.json`
- Verify API key is valid and has quota

**Port 8000 already in use:**
- Change port: `uvicorn backend.main:app --reload --port 8001`
- Update frontend `vite.config.ts` proxy target if needed

### Frontend Issues

**Cannot connect to backend:**
- Ensure backend is running
- Check `vite.config.ts` proxy configuration
- Try `http://localhost:8000` directly in browser

**npm install errors:**
- Use Node.js 18+
- Try deleting `node_modules` and `package-lock.json`, then `npm install` again

### Data Issues

**Question bank is empty:**
- Run: `python -m backend.services.ingest`
- Check CSV files exist in `src/data/questions_and_answers/`
- Verify DATA_DIR environment variable

## Next Steps

After setup is complete:

1. **Test the flow:**
   - Landing → Document Setup → CV Improve → Interview
   - Or: Landing → Document Setup → Skip to Interview

2. **Check Dashboard:**
   - Complete a CV analysis or interview
   - View readiness scores and progress

3. **Test Voice Features:**
   - Use mic button in Interview Room
   - Ensure browser supports Web Speech API (Chrome/Edge recommended)

## Development Commands

```bash
# Backend
uvicorn backend.main:app --reload --port 8000

# Frontend
cd app && npm run dev

# Run ingestion again
python -m backend.services.ingest

# Check database
# SQLite database is at backend/data/app.db
# You can inspect it with: sqlite3 backend/data/app.db
```

## Production Deployment

For production:
- Build frontend: `cd app && npm run build`
- Serve backend with production WSGI server (Gunicorn, etc.)
- Set up proper environment variables
- Use PostgreSQL instead of SQLite for production
