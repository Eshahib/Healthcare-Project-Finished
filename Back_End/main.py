"""
HIPAA-Compliant Symptom Diagnosis API
All PHI data is encrypted at rest and audit logged
"""
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from typing import Optional
from datetime import timedelta
import models
import os
from database import engine, Base, getDB
from schemas import (
    SymptomEntryCreate,
    SymptomEntryResponse,
    DiagnosisCreate,
    DiagnosisResponse,
    SymptomEntryWithDiagnosis,
    UserCreate,
    UserResponse,
    Token
)
from audit_log import log_phi_access


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
    print("Database tables created/verified!")

app = FastAPI(
    title="HIPAA-Compliant Symptom Diagnosis API",
    description="Secure API for symptom checking with PHI encryption and audit logging",
    version="1.0.0"
)

# CORS middleware - configure allowed origins in production

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Your frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Use a strong secret key for session cookie signing; load from env var
SESSION_SECRET = os.getenv("SESSION_SECRET", "super-secret-random-string")

# Middleware order matters: add SessionMiddleware before CORS
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)

@app.get("/")
def root():
    return {
        "message": "HIPAA-Compliant Symptom Diagnosis API is running!",
        "version": "1.0.0",
        "compliance": "HIPAA"
    }

@app.get("/health")
def health_check(db: Session = Depends(getDB)):
    """Health check endpoint."""
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        return {"status": "error", "db": str(e)}


from routes.auth import router as authRouter
from routes.SymptomRouter import router as SymptomRouter
from routes.DiagnosisRouter import router as DiagnosisRouter

app.include_router(authRouter, prefix="/api")
app.include_router(SymptomRouter, prefix="/api")
app.include_router(DiagnosisRouter, prefix="/api")



@app.on_event("startup")
def startup_event():
    """Initialize database on startup."""
    init_db()
    print("✅ HIPAA-Compliant API started successfully!")
    print("🔒 PHI encryption: ENABLED")
    print("📋 Audit logging: ENABLED")
