from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import Diagnosis
from pydynamicModels import DiagnosisRead, SymptomEntryRead
from database import getDB
from pydynamicModels import DiagnosisRead, DiagnosisCreate
from typing import List


router = APIRouter()



#this migh tneed to chnage base on front end
@router.get("/diagnoses/{symptom_entry_id}", response_model=DiagnosisRead)
def get_diagnosis(symptom_entry_id: int, db: Session = Depends(getDB)):
    diagnosis = db.query(Diagnosis).filter(Diagnosis.symptom_entry_id == symptom_entry_id).first()
    if not diagnosis:
        raise HTTPException(status_code=404, detail="Diagnosis not found for given symptom entry")
    return diagnosis


#returns list of diagnosis
@router.get("/list/diagnoses/", response_model=List[DiagnosisRead])
def list_diagnoses(skip: int = 0, limit: int = 10, db: Session = Depends(getDB)):
    diagnoses = db.query(Diagnosis).offset(skip).limit(limit).all()
    return diagnoses


@router.post("/add/diagnoses/", response_model=DiagnosisRead)
def add_diagnosis(diagnosis_in: DiagnosisCreate, db: Session = Depends(getDB)):
    
    symptom_entry = db.query(SymptomEntryRead).filter(SymptomEntryRead.id == diagnosis_in.symptom_entry_id).first()
    if not symptom_entry:
        raise HTTPException(status_code=404, detail="Symptom entry not found")

    existing = db.query(Diagnosis).filter(Diagnosis.symptom_entry_id == diagnosis_in.symptom_entry_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Diagnosis already exists for this symptom entry")

    diagnosis = Diagnosis(
        symptom_entry_id=diagnosis_in.symptom_entry_id,
        diagnosis_text=diagnosis_in.diagnosis_text,
    )

    db.add(diagnosis)
    db.commit()
    db.refresh(diagnosis)
    return diagnosis