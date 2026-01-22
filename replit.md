# PrepAIr - AI-Powered Career Preparation Platform

## Overview
PrepAIr is a full-stack application that helps job seekers optimize their CVs and practice interviews using Google Gemini 2.5 Pro AI via Replit AI Integrations (no personal API key needed).

## Project Structure
```
.
├── app/              # React + Vite + TypeScript frontend (port 5000)
│   └── src/
│       ├── pages/        # Page components (Landing, DocumentSetup, etc.)
│       ├── components/   # Shared UI components (Toast, ErrorBoundary, LoadingSpinner)
│       ├── api/          # API client
│       └── voice/        # TTS/STT utilities
├── backend/          # FastAPI + SQLite backend (port 8000)
│   ├── routers/          # API route handlers
│   ├── services/         # Business logic (gemini_client, cv_analyzer, scoring)
│   └── models.py         # SQLModel database models
├── docs/             # API documentation
├── src/              # Legacy data files (CSV sources)
└── tests/            # Test files
```

## Tech Stack
- **Frontend**: React 18, Vite 5, TypeScript, React Router v6
- **Backend**: FastAPI, SQLModel, SQLite, Pydantic
- **AI**: Google Gemini 2.5 Pro (via Replit AI Integrations)
- **UI**: Modern gradient design with toast notifications

## Running the Application
The workflow runs both servers:
- Frontend: `cd app && npm run dev` (port 5000)
- Backend: `uvicorn backend.main:app --host localhost --port 8000`

## Environment Variables
- `AI_INTEGRATIONS_GEMINI_API_KEY`: Auto-provided by Replit AI Integrations
- `AI_INTEGRATIONS_GEMINI_BASE_URL`: Auto-provided by Replit AI Integrations
- `VITE_BACKEND_URL`: Backend URL (default: http://localhost:8000)

## Key Features
1. CV upload and AI-powered analysis
2. Job description matching with role profile extraction
3. AI-powered interview practice with scoring and feedback
4. CV improvement suggestions with before/after examples
5. Progress tracking dashboard
6. Modern UI with toast notifications, error boundaries, and loading states

## Recent Changes (January 2026)
- Integrated Gemini AI via Replit AI Integrations (no API key needed)
- Added toast notification system replacing all alert() calls
- Created ErrorBoundary and LoadingSpinner components
- Enhanced CV analysis with AI-powered gap detection and suggestions
- Added /api/cv/improve endpoint for detailed CV improvements
- Added input validation with field length limits
- Added global exception handlers for better error messages
- Modern gradient UI design (purple/blue theme)

## User Preferences
- Step-by-step approach preferred
- This is a prototype without authentication
- Uses Replit's built-in AI integrations (charged to credits)
