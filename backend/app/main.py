from fastapi import FastAPI
from app.api import endpoints

app = FastAPI(
    title="API Change Impact Analyzer",
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

app.include_router(endpoints.router, prefix="/api/v1")
