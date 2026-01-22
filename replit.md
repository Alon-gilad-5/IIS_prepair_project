# PrepAIr - AI-Powered Career Preparation Platform

## Overview
PrepAIr is a full-stack application that helps job seekers optimize their CVs and practice interviews using Google Gemini 2.5 Pro AI.

## Project Structure
```
.
├── app/              # React + Vite + TypeScript frontend (port 5000)
├── backend/          # FastAPI + SQLite backend (port 8000)
├── docs/             # API documentation
├── src/              # Legacy data files (CSV sources)
└── tests/            # Test files
```

## Tech Stack
- **Frontend**: React 18, Vite 5, TypeScript, React Router v6
- **Backend**: FastAPI, SQLModel, SQLite, Pydantic
- **AI**: Google Gemini 2.5 Pro

## Running the Application
The workflow runs both servers:
- Frontend: `cd app && npm run dev` (port 5000)
- Backend: `uvicorn backend.main:app --host localhost --port 8000`

## Environment Variables
- `GEMINI_API_KEY`: Required for AI features
- `VITE_BACKEND_URL`: Backend URL (default: http://localhost:8000)

## Key Features
1. CV upload and analysis
2. Job description matching
3. AI-powered interview practice
4. Progress tracking dashboard

## Recent Changes
- Configured for Replit environment
- Frontend set to port 5000 with proxy support
- Backend CORS configured to allow all origins
