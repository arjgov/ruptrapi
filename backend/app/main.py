from fastapi import FastAPI
from app.core.config import settings
from app.api.api import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Tool to analyze breaking changes between API spec versions",
    version="0.1.0"
)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "ruptrapi"}

@app.get("/")
def root():
    return {
        "message": "Welcome to Api Change Impact Analyzer",
        "docs": "/docs",
        "redoc": "/redoc"
    }

app.include_router(api_router, prefix="/ruptrapi/v1")
