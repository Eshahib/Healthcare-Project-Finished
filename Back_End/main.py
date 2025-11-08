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


from auth import router as asuthRouter
app.include_router(asuthRouter, prefix="/api")

@app.post("/api/symptoms", response_model=SymptomEntryResponse, status_code=status.HTTP_201_CREATED)
def create_symptom_entry(
    symptom_data: SymptomEntryCreate,
    request: Request,
    db: Session = Depends(getDB)
):
    """
    Create a new symptom entry with encrypted PHI storage.
    All PHI data is encrypted at rest and access is audit logged.
    """
    try:
        # Create symptom entry with encrypted data
        symptom_entry = models.SymptomEntry()
        symptom_entry.symptoms = symptom_data.symptoms
        symptom_entry.comments = symptom_data.comments
        symptom_entry.user_id = symptom_data.user_id
        
        db.add(symptom_entry)
        db.commit()
        db.refresh(symptom_entry)
        
        # Audit log PHI creation (file log)
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        log_phi_access(
            user_id=symptom_entry.user_id,
            action="CREATE",
            resource_type="SymptomEntry",
            resource_id=symptom_entry.id,
            ip_address=client_ip,
            user_agent=user_agent,
            details=f"Created symptom entry with {len(symptom_data.symptoms)} symptoms",
            success="SUCCESS"
        )
        
        # Audit log PHI creation (database)
        audit_entry = models.AuditLog(
            user_id=symptom_entry.user_id,
            symptom_entry_id=symptom_entry.id,
            action="CREATE",
            resource_type="SymptomEntry",
            resource_id=symptom_entry.id,
            ip_address=client_ip,
            user_agent=user_agent,
            details=f"Created symptom entry with {len(symptom_data.symptoms)} symptoms",
            success="SUCCESS"
        )
        db.add(audit_entry)
        db.commit()
        
        # Return response with decrypted data
        response = SymptomEntryResponse(
            id=symptom_entry.id,
            user_id=symptom_entry.user_id,
            symptoms=symptom_entry.symptoms,
            comments=symptom_entry.comments,
            created_at=symptom_entry.created_at
        )
        
        # TODO: Add LLM analysis here in the future
        
        return response
    except Exception as e:
        db.rollback()
        log_phi_access(
            user_id=symptom_data.user_id,
            action="CREATE",
            resource_type="SymptomEntry",
            resource_id=0,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            details=f"Failed to create symptom entry: {str(e)}",
            success="FAILED"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create symptom entry: {str(e)}"
        )


@app.get("/api/symptoms/{symptom_id}", response_model=SymptomEntryWithDiagnosis)
def get_symptom_entry(
    symptom_id: int,
    request: Request,
    db: Session = Depends(getDB)
):
    """
    Get a symptom entry by ID.
    Access is audit logged for HIPAA compliance.
    """
    try:
        symptom_entry = db.query(models.SymptomEntry).filter(
            models.SymptomEntry.id == symptom_id
        ).first()
        
        if not symptom_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Symptom entry not found"
            )
        
        # Audit log PHI access (file log)
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        log_phi_access(
            user_id=symptom_entry.user_id,
            action="READ",
            resource_type="SymptomEntry",
            resource_id=symptom_entry.id,
            ip_address=client_ip,
            user_agent=user_agent,
            details="Read symptom entry",
            success="SUCCESS"
        )
        
        # Audit log PHI access (database)
        audit_entry = models.AuditLog(
            user_id=symptom_entry.user_id,
            symptom_entry_id=symptom_entry.id,
            action="READ",
            resource_type="SymptomEntry",
            resource_id=symptom_entry.id,
            ip_address=client_ip,
            user_agent=user_agent,
            details="Read symptom entry",
            success="SUCCESS"
        )
        db.add(audit_entry)
        db.commit()
        
        # Get diagnosis if exists
        diagnosis_response = None
        if symptom_entry.diagnosis:
            diagnosis_response = DiagnosisResponse(
                id=symptom_entry.diagnosis.id,
                symptom_entry_id=symptom_entry.diagnosis.symptom_entry_id,
                diagnosis_text=symptom_entry.diagnosis.diagnosis_text,
                confidence_score=symptom_entry.diagnosis.confidence_score,
                possible_conditions=symptom_entry.diagnosis.possible_conditions,
                recommendations=symptom_entry.diagnosis.recommendations,
                created_at=symptom_entry.diagnosis.created_at
            )
        
        return SymptomEntryWithDiagnosis(
            id=symptom_entry.id,
            user_id=symptom_entry.user_id,
            symptoms=symptom_entry.symptoms,
            comments=symptom_entry.comments,
            created_at=symptom_entry.created_at,
            diagnosis=diagnosis_response
        )
    except HTTPException:
        raise
    except Exception as e:
        log_phi_access(
            user_id=None,
            action="READ",
            resource_type="SymptomEntry",
            resource_id=symptom_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            details=f"Failed to read symptom entry: {str(e)}",
            success="FAILED"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve symptom entry: {str(e)}"
        )


@app.post("/api/diagnoses", response_model=DiagnosisResponse, status_code=status.HTTP_201_CREATED)
def create_diagnosis(
    diagnosis_data: DiagnosisCreate,
    request: Request,
    db: Session = Depends(getDB)
):
    """
    Create a diagnosis for a symptom entry (manual creation).
    Diagnosis text contains PHI and is encrypted at rest.
    """
    try:
        # Verify symptom entry exists
        symptom_entry = db.query(models.SymptomEntry).filter(
            models.SymptomEntry.id == diagnosis_data.symptom_entry_id
        ).first()
        
        if not symptom_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Symptom entry not found"
            )
        
        # Create diagnosis with encrypted data
        diagnosis = models.Diagnosis()
        diagnosis.symptom_entry_id = diagnosis_data.symptom_entry_id
        diagnosis.diagnosis_text = diagnosis_data.diagnosis_text
        diagnosis.confidence_score = diagnosis_data.confidence_score
        diagnosis.possible_conditions = diagnosis_data.possible_conditions
        diagnosis.recommendations = diagnosis_data.recommendations
        
        db.add(diagnosis)
        db.commit()
        db.refresh(diagnosis)
        
        # Audit log (file log)
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        log_phi_access(
            user_id=symptom_entry.user_id,
            action="CREATE",
            resource_type="Diagnosis",
            resource_id=diagnosis.id,
            ip_address=client_ip,
            user_agent=user_agent,
            details="Created diagnosis",
            success="SUCCESS"
        )
        
        # Audit log (database)
        audit_entry = models.AuditLog(
            user_id=symptom_entry.user_id,
            symptom_entry_id=symptom_entry.id,
            action="CREATE",
            resource_type="Diagnosis",
            resource_id=diagnosis.id,
            ip_address=client_ip,
            user_agent=user_agent,
            details="Created diagnosis",
            success="SUCCESS"
        )
        db.add(audit_entry)
        db.commit()
        
        return DiagnosisResponse(
            id=diagnosis.id,
            symptom_entry_id=diagnosis.symptom_entry_id,
            diagnosis_text=diagnosis.diagnosis_text,
            confidence_score=diagnosis.confidence_score,
            possible_conditions=diagnosis.possible_conditions,
            recommendations=diagnosis.recommendations,
            created_at=diagnosis.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create diagnosis: {str(e)}"
        )


@app.on_event("startup")
def startup_event():
    """Initialize database on startup."""
    init_db()
    print("✅ HIPAA-Compliant API started successfully!")
    print("🔒 PHI encryption: ENABLED")
    print("📋 Audit logging: ENABLED")
