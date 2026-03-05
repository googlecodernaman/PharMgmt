"""FastAPI application entry point."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from pharmgmt import __version__
from pharmgmt.api.routes import router
from pharmgmt.config import get_settings
from pharmgmt.db import init_db
from pharmgmt.logging_config import setup_logging

app = FastAPI(
    title="PharMgmt",
    description="Pharmacy Bill Management System",
    version=__version__,
)

# CORS — allow localhost origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:*", "http://127.0.0.1:*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

# Static files for future frontend
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.on_event("startup")
def startup_event():
    """Initialize database and logging on startup."""
    settings = get_settings()
    setup_logging(settings.LOG_DIR, settings.LOG_LEVEL)
    init_db(settings.DATABASE_URL)
