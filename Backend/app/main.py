from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from . import models
from .routes.assessments import router as assessments_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI GRC Assessment API",
    description="Prototype API for AI model intake and GRC assessment.",
    version="0.1.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(assessments_router)

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "AI GRC Assessment API"}
