"""
Clean Architecture FastAPI Application.

This module demonstrates clean architecture principles:
- Separation of concerns (domain, use cases, infrastructure, API)
- Dependency inversion (high-level doesn't depend on low-level)
- Single responsibility (each layer has one reason to change)
- Python philosophy (explicit, simple, readable)
"""

import logging

from fastapi import FastAPI

from api.routes import router as chat_router

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Azure DevOps PBI Extraction API",
    version="2.0.0",
    description="Clean Architecture implementation for conversational PBI extraction",
)

# Include routers
app.include_router(chat_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "2.0.0"}


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Azure DevOps PBI Extraction API",
        "version": "2.0.0",
        "architecture": "Clean Architecture",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
