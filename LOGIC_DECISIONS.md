# PrepAIr Logic Decisions & Architecture

This document explains the key architectural and design decisions made in the PrepAIr project.

## Technology Stack

### Backend: FastAPI + SQLite
**Decision:** FastAPI with SQLModel for type-safe database operations  
**Rationale:**
- FastAPI provides automatic OpenAPI docs, async support, and type validation
- SQLModel combines SQLAlchemy with Pydantic for unified models
- SQLite is sufficient for MVP and simplifies deployment (single file)
- Can migrate to PostgreSQL later without code changes

### Frontend: React + Vite + TypeScript
**Decision:** React with TypeScript for type safety  
**Rationale:**
- React is widely used and well-documented
- TypeScript catches errors at compile time
- Vite provides fast HMR and optimized builds
- React Router for client-side routing

### LLM: Google Gemini 2.5 Pro
**Decision:** Gemini 2.5 Pro for all LLM operations  
**Rationale:**
- Supports structured JSON output with strict schemas
- Good performance for role extraction, scoring, and follow-up generation
- Fallback heuristics implemented when API is unavailable
- No OpenAI dependency reduces costs and API key management

## Database Design

### UUID vs Integer IDs
**Decision:** UUID strings for user-facing IDs, SQLite auto-increment internally  
**Rationale:**
- UUIDs prevent ID enumeration attacks
- Easier to merge databases or migrate users
- Visible in API responses, hides internal database structure

### JSON Fields in Database
**Decision:** Store complex data as JSON strings in text fields  
**Rationale:**
- SQLite has limited JSON support
- Allows flexibility without schema migrations
- Parsed on read, validated in application layer
- Examples: `plan_json`, `score_json`, `topics_json`

### Models Structure
**Decision:** 10 core models covering CV versions, job specs, interviews, progress  
**Rationale:**
- **cv_versions**: Track CV evolution with parent-child relationships
- **cv_analysis_results**: Separate analysis from CV storage for historical tracking
- **question_bank**: Denormalized storage with `id` as "code:123" or "open:456"
- **interview_turns**: Immutable turn records for audit trail
- **user_readiness_snapshots**: Time-series data for trend analysis

## Question Selection Logic

### Weighted Sampling with Diversity
**Decision:** Match score based on topic intersection with role profile weights  
**Rationale:**
- Ensures questions align with job requirements
- Diversity constraint (Jaccard similarity) prevents repetitive topics
- Excludes recently asked questions (last 3 sessions or 7 days)
- Adaptive candidates for code questions (Easy/Medium/Hard per slot)

### Plan Structure
**Decision:** Store full plan JSON with candidates and selected questions  
**Rationale:**
- Enables adaptive difficulty during interview
- Preserves original selection logic for analysis
- Allows mid-interview question swaps based on performance

## Scoring System

### Heuristics + LLM Hybrid
**Decision:** MVP uses Gemini for detailed scoring, fallback heuristics if unavailable  
**Rationale:**
- LLM provides nuanced rubric (clarity, relevance, structure, correctness, depth)
- Fallback ensures system works without API key
- For code questions: score reasoning/approach, NOT code execution
- Reference solution used for evaluation, not compilation

### Score Normalization
**Decision:** All scores are floats 0.0-1.0, converted to 0-100 for display  
**Rationale:**
- Consistent representation across all scoring functions
- Easy to weight different components (CV 40%, Interview 50%, Practice 10%)
- Readiness score computed from weighted average

## Readiness Score Calculation

### Weighted Components
**Decision:** CV Score (40%) + Interview Score (50%) + Practice Score (10%)  
**Rationale:**
- **CV Score**: Measures alignment with job requirements (primary signal)
- **Interview Score**: Reflects actual performance (strong signal)
- **Practice Score**: Encourages engagement but lower weight (weak signal)
- Snapshot created after CV analysis and interview end for tracking

### Practice Score Heuristics
**Decision:** Based on session count, recency, and trend  
**Rationale:**
- Rewards active practice
- Recency bonus (sessions in last 7 days)
- Trend bonus for consistent improvement

## CV Analysis Flow

### Two-Step Process: Ingest → Analyze
**Decision:** Separate CV ingestion from analysis  
**Rationale:**
- Allows multiple analyses of same CV against different jobs
- Enables CV versioning without re-analyzing
- Role profile extracted once per job spec (cached by JD hash)

### Role Profile Extraction
**Decision:** Gemini extracts structured role profile from CV + JD  
**Rationale:**
- Captures must-have vs nice-to-have topics
- Generates topic weights for question matching
- Fallback keyword extraction if Gemini fails

## Interview Flow

### Mode: Direct vs After CV
**Decision:** Two modes for flexibility  
**Rationale:**
- **Direct**: Quick interview without CV analysis
- **After CV**: Personalized based on CV gaps and strengths
- Mode stored in session for analysis later

### Turn-Based Architecture
**Decision:** Each answer creates a turn record, plan determines progression  
**Rationale:**
- Immutable turn history for audit and replay
- Follow-up questions generated on-demand (not pre-planned)
- Progress tracked as `turn_index / total` from plan

## Voice Integration

### Web Speech API (No External Services)
**Decision:** Use browser-native TTS and STT  
**Rationale:**
- No additional API costs
- Works offline (speech synthesis)
- Falls back to text input if unsupported
- Chrome/Edge have best support

### TTS for Questions
**Decision:** Text-to-speech for question reading  
**Rationale:**
- More realistic interview experience
- Accessibility for visually impaired
- "Repeat Question" button replays TTS

## Frontend State Management

### LocalStorage for User Session
**Decision:** Store `userId`, `cvVersionId`, `jobSpecId` in localStorage  
**Rationale:**
- Simple session persistence across page reloads
- No backend session management needed for MVP
- Can migrate to JWT tokens later

### API Client Pattern
**Decision:** Centralized `api/client.ts` with typed functions  
**Rationale:**
- Single source of truth for API endpoints
- Easy to add authentication headers later
- Error handling in one place

## Code Question Interface

### Whiteboard + Keyboard Popup
**Decision:** Modal popup with code editor for code questions  
**Rationale:**
- Provides dedicated space for coding
- Mimics real interview coding environments
- Keyboard shortcuts for common operations
- Code submitted separately from verbal explanation

## Error Handling & Fallbacks

### Graceful Degradation
**Decision:** System continues with heuristics if Gemini fails  
**Rationale:**
- MVP remains functional without API key
- Fallback role profiles use keyword matching
- Fallback scoring uses answer length and structure
- All critical paths have fallbacks

### Safe JSON Parsing
**Decision:** Always validate and clean LLM JSON responses  
**Rationale:**
- Remove markdown code blocks
- Retry on parse errors (up to max_retries)
- Default values if parsing fails completely

## Data Ingestion

### Idempotent Upsert
**Decision:** Questions upserted by `id` (e.g., "code:123")  
**Rationale:**
- Safe to re-run ingestion
- Updates existing questions if CSV changes
- Prevents duplicates while allowing updates

### CSV Normalization
**Decision:** Normalize topics to JSON array, handle various formats  
**Rationale:**
- CSV files have inconsistent topic formats (JSON, comma-separated, single)
- Normalize on ingest for consistent querying
- Store as JSON string in database

## Security Considerations

### No Authentication in MVP
**Decision:** User IDs generated client-side, no login required  
**Rationale:**
- Faster MVP development
- Can add OAuth/JWT later without changing core logic
- LocalStorage used for simplicity

### CORS Configuration
**Decision:** Allow specific dev origins in CORS middleware  
**Rationale:**
- Prevents cross-origin attacks in production
- Relaxed for development (localhost:5173, :3000)
- Should restrict to production domain in deployment

## Performance Optimizations

### Batch Commits in Ingestion
**Decision:** Commit every 100 records during CSV import  
**Rationale:**
- Reduces database lock contention
- Faster than commit-per-record
- Balance between speed and transaction safety

### Lazy Role Profile Extraction
**Decision:** Extract role profile on-demand, cache by JD hash  
**Rationale:**
- Avoids expensive LLM calls during CV ingestion
- Multiple CVs for same job reuse profile
- Profile stored in `job_specs.jd_profile_json`

## Future Considerations

### Not Implemented (Intentionally)
- **Feedback page**: Placeholder only, to be implemented later
- **Code execution**: Scoring based on approach, not running code
- **Real-time collaboration**: Single-user MVP
- **Multi-language support**: English only for MVP

### Scalability Path
- SQLite → PostgreSQL for concurrent writes
- LocalStorage → JWT tokens for authentication
- In-memory caching for frequently accessed data
- Background jobs for heavy processing (readiness calculations)

## Testing Strategy (MVP)

### Manual Testing
**Decision:** No automated tests in MVP  
**Rationale:**
- Faster development cycle
- Focus on functionality over test coverage
- Can add unit/integration tests later

### Data Validation
**Decision:** Pydantic schemas for request/response validation  
**Rationale:**
- Automatic API documentation (OpenAPI)
- Type safety without manual checks
- Clear error messages for API consumers
