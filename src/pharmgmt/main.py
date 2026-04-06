"""FastAPI application entry point."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from pharmgmt import __version__
from pharmgmt.api.routes import router
from pharmgmt.config import get_settings
from pharmgmt.db import init_db, migrate_db
from pharmgmt.logging_config import setup_logging

app = FastAPI(
    title="PharMgmt",
    description="Pharmacy Bill Management System",
    version=__version__,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

# Static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def root_redirect():
    """Redirect root to dashboard."""
    return RedirectResponse(url="/static/index.html#/dashboard")


@app.on_event("startup")
def startup_event():
    """Initialize database, run migrations, and configure logging on startup."""
    settings = get_settings()
    setup_logging(settings.LOG_DIR, settings.LOG_LEVEL)
    init_db(settings.DATABASE_URL)
    migrate_db(settings.DATABASE_URL)
