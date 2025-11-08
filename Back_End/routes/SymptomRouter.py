from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
import models
from database import getDB
from schemas import SymptomEntryCreate, SymptomEntryResponse, SymptomEntryWithDiagnosis, DiagnosisResponse, DiagnosisCreate
from audit_log import log_phi_access

router = APIRouter()

@router.post("/symptoms", response_model=SymptomEntryResponse, status_code=status.HTTP_201_CREATED)
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
        print("EHRERERERERER")
        print(symptom_data.user_email)
        user = db.query(models.User).filter(models.User.email == symptom_data.user_email).first()

        if not user:
            raise HTTPException(status_code=404, detail="could not find the user")
        
        symptom_entry = models.SymptomEntry()
        symptom_entry.symptoms = symptom_data.symptoms
        symptom_entry.comments = symptom_data.comments
        symptom_entry.user_id = user.id
        
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


@router.get("/symptoms/{symptom_id}", response_model=SymptomEntryWithDiagnosis)
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

