from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
import models
from database import getDB
from schemas import DiagnosisCreate, DiagnosisResponse
from audit_log import log_phi_access

router = APIRouter()

@router.post("/diagnoses", response_model=DiagnosisResponse, status_code=status.HTTP_201_CREATED)
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
