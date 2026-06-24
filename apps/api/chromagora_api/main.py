"""Chromagora OS API — FastAPI application."""

import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from chromagora_api.core.config import settings
from chromagora_api.routes.health import router as health_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Chromagora OS API v{settings.version} starting...")
    logger.info(f"Environment: {settings.chromagora_env}")
    from chromagora_api.core.supabase import is_supabase_configured
    logger.info(f"Supabase configured: {is_supabase_configured()}")
    yield


app = FastAPI(
    title="Chromagora OS",
    description="Multi-agent operating system for SMBs — API",
    version=settings.version,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(health_router)
