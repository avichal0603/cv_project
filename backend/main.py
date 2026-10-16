"""FastAPI Application Entry Point for Screen Moiré Removal Application."""

import logging
import os
import sys
from pathlib import Path

# Ensure backend root is on sys.path
backend_dir = str(Path(__file__).resolve().parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

try:
    from api.routes import router as api_router
except ImportError:
    from backend.api.routes import router as api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("moire_removal")

app = FastAPI(
    title="Screen Moiré Removal API",
    description="Backend microservice for removing screen moiré patterns using spatial, frequency, wavelet, and edge-aware adaptive filtering.",
    version="1.0.0",
)

# CORS configuration - Allow all origins including Vercel and local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router, prefix="/api")

# Mount synthetic dataset directory for direct static access if exists
generated_dir = os.path.join(backend_dir, "datasets", "generated")
if os.path.exists(generated_dir):
    app.mount("/datasets/generated", StaticFiles(directory=generated_dir), name="generated_datasets")


@app.get("/", summary="Root Status")
async def root():
    """Service status and quick links."""
    return {
        "service": "Screen Moiré Removal API",
        "status": "online",
        "docs_url": "/docs",
        "api_endpoints": [
            "POST /api/process",
            "POST /api/evaluate",
            "GET /api/algorithms",
            "POST /api/spectrum",
            "POST /api/compare",
            "GET /api/health",
        ]
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
