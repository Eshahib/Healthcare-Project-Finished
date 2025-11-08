"""
HIPAA-Compliant Symptom Diagnosis API
All PHI data is encrypted at rest and audit logged
"""
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional
from datetime import timedelta
import models
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
from auth import (
    authenticate_user,
    get_password_hash,
    create_access_token,
    get_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def get_symptom_data_for_api(symptom_entry: models.SymptomEntry) -> dict:
    """
    Collects decrypted symptoms and comments into a single data structure
    ready for JSON serialization to send to external APIs.
    
    Args:
        symptom_entry: SymptomEntry model instance
        
    Returns:
        dict: Combined data structure with symptoms and comments
        {
            "symptoms": ["Fever", "Cough", ...],
            "comments": "Patient's free response text",
            "symptom_entry_id": 1
        }
    """
    # Accessing .symptoms and .comments automatically decrypts them
    decrypted_symptoms = symptom_entry.symptoms  # List[str] - auto-decrypted
    decrypted_comments = symptom_entry.comments  # Optional[str] - auto-decrypted
    
    # Combine into a single data structure
    combined_data = {
        "symptoms": decrypted_symptoms,
        "comments": decrypted_comments if decrypted_comments else "",
        "symptom_entry_id": symptom_entry.id
    }
    
    return combined_data

def get_symptom_data_json_string(symptom_entry: models.SymptomEntry) -> str:
    """
    Returns the combined symptom data as a JSON string ready to send to APIs.
    
    Args:
        symptom_entry: SymptomEntry model instance
        
    Returns:
        str: JSON string representation of the combined data
    """
    import json
    data = get_symptom_data_for_api(symptom_entry)
    return json.dumps(data, ensure_ascii=False)

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
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Add your frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(getDB)):
    """Get the current authenticated user from JWT token."""
    from jose import JWTError, jwt
    from auth import SECRET_KEY, ALGORITHM
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


@app.post("/api/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(getDB)):
    """Register a new user."""
    try:
        # Check if username already exists
        existing_user = db.query(models.User).filter(models.User.username == user_data.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Check if email already exists (if provided)
        if user_data.email:
            existing_email = db.query(models.User).filter(models.User.email == user_data.email).first()
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        new_user = models.User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return UserResponse(
            id=new_user.id,
            username=new_user.username,
            email=new_user.email,
            created_at=new_user.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@app.post("/api/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(getDB)):
    """Login and get access token."""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/auth/me", response_model=UserResponse)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    """Get current user information."""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        created_at=current_user.created_at
    )


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
