"""Main entry point for PrepAIr backend API server."""

from src.api.interview import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
