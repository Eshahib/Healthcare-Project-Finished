from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
import models
from database import getDB
from schemas import DiagnosisCreate, DiagnosisResponse
from audit_log import log_phi_access
import os
import requests
from dotenv import load_dotenv
import json
from encryption import encrypt_phi
from pydantic import BaseModel
import time
import re

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



load_dotenv()

NEURALSEEK_API_URL = os.getenv("NEURALSEEK_API_URL", "https://stagingapi.neuralseek.com/v1/stony4/maistro")
NEURALSEEK_API_KEY = os.getenv("NEURALSEEK_API_KEY")

router = APIRouter()

class SymptomInput(BaseModel):
    symptoms: list[str]
    username: str
    symptomEntry: int

@router.post("/make/diagnose")
async def diagnose(input_data: SymptomInput, request: Request, db: Session = Depends(getDB)):
    payload = {
        "agent": "Healthcare",
        "params": [
            {"name": "symptoms", "value": input_data.symptoms}
        ]
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "apikey": NEURALSEEK_API_KEY
    }
    max_retries = 3
    print(input_data)
    for attempt in range(max_retries):
        try:
            response = requests.post(NEURALSEEK_API_URL, headers=headers, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()

            diagnosis_text = data.get("answer")
            if not diagnosis_text:
                raise HTTPException(status_code=502, detail="Invalid response from NeuralSeek API")

            encryptedText = encrypt_phi(diagnosis_text)

            user = db.query(models.User).filter(models.User.username == input_data.username).first()
            print(user)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            symptomentry = db.query(models.SymptomEntry).filter(models.SymptomEntry.id == input_data.symptomEntry).first()
            if not symptomentry:
                raise HTTPException(status_code=404, detail="Symptom entry not found")
            print(symptomentry)
            create_payload = DiagnosisCreate(
                symptom_entry_id=input_data.symptomEntry,
                diagnosis_text=diagnosis_text,
                confidence_score=None,
                possible_conditions=None,
                recommendations=None
            )

            # ✅ Important: await or return the diagnosis creation properly
            result = create_diagnosis(
                diagnosis_data=create_payload,
                request=request,
                db=db
            )
            return result

        except requests.exceptions.ReadTimeout:
            print(f"Timeout, retry {attempt + 1}...")
            time.sleep(2)

        except Exception as e:
            print(f"Error during attempt {attempt + 1}: {e}")
            time.sleep(2)

    # ✅ Always return something even if retries fail
    raise HTTPException(status_code=504, detail="NeuralSeek API timed out after multiple attempts")

