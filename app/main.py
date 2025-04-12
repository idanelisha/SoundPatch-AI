from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.routes import audio, auth, health
from app.core.logging import logger

settings = get_settings()

def create_application() -> FastAPI:
    logger.info("Creating FastAPI application", extra={"settings": settings.dict()})
    
    application = FastAPI(
        title="SoundPatch AI API",
        description="API for audio processing and analysis",
        version="1.0.0",
        docs_url="/api/v1/docs",
        redoc_url="/api/v1/redoc",
        openapi_url="/api/v1/openapi.json",
        swagger_ui_parameters={"persistAuthorization": True}
    )

    # Configure CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, replace with specific origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    logger.info("Registering routes")
    application.include_router(health.router, prefix="/api/v1")
    application.include_router(auth.router, prefix="/api/v1")
    application.include_router(audio.router, prefix="/api/v1")
    logger.info("Routes registered successfully")

    @application.get("/")
    async def root():
        """Root endpoint."""
        logger.debug("Root endpoint accessed")
        return {"message": "Welcome to SoundPatch AI API"}

    @application.get("/health")
    async def health_check():
        logger.debug("Health check endpoint accessed")
        return {"status": "healthy"}

    logger.info("Application created successfully")
    return application

app = create_application() 