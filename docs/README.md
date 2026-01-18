# PrepAIr Documentation

This folder contains API and technical documentation for PrepAIr.

## 📄 Files

### `api.yaml`
Complete OpenAPI 3.0 specification for all backend API endpoints.

**Usage:**
- View in Swagger UI: `http://localhost:8000/docs` (FastAPI auto-generates)
- Import into Postman/Insomnia for API testing
- Reference for frontend API client implementation

**Endpoints Documented:**
- `/api/users/*` - User management
- `/api/cv/*` - CV operations
- `/api/jd/*` - Job description management
- `/api/interview/*` - Interview sessions
- `/api/progress/*` - Progress tracking

## 📚 Related Documentation

- **[../README.md](../README.md)** - Project overview & quick start
- **[../SETUP_WORKFLOW.md](../SETUP_WORKFLOW.md)** - Detailed setup instructions
- **[../LOGIC_DECISIONS.md](../LOGIC_DECISIONS.md)** - Architecture decisions
- **[../backend/README.md](../backend/README.md)** - Backend documentation
- **[../app/README.md](../app/README.md)** - Frontend documentation

## 🔧 Viewing API Docs

### Interactive (Swagger UI)
Start backend and visit: `http://localhost:8000/docs`

### Interactive (ReDoc)
Start backend and visit: `http://localhost:8000/redoc`

### YAML File
Open `api.yaml` in any text editor or YAML viewer.

## 📝 Notes

- All endpoints use Gemini 2.5 Pro (no OpenAI)
- JSON request/response formats
- Error responses follow FastAPI standard format
- CORS enabled for `localhost:5173` (frontend)
