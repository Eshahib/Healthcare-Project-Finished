from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models
from database import getDB
from pydynamicModels import SymptomEntryCreate, SymptomEntryRead

router = APIRouter()

@router.post("/add/symptoms", response_model=SymptomEntryRead)
def submit_solutions(
    entry: SymptomEntryCreate, 
    db: Session = Depends(getDB)
):
    
    #change when we get real user
    user_id = 1
    symptom_entry = models.SymptomEntry(user_id=user_id)

    db.add(symptom_entry)
    db.flush()  

    #Link all selected symptoms (standard or custom) to this entry
    #need to add user id here
    for symptom in entry.symptoms:
        db.add(models.EntrySymptom(
            symptom_entry_id=symptom_entry.id,
            symptom_id=symptom.symptom_id,
            custom_symptom=symptom.custom_symptom,
            user_id=user_id
        ))
    db.commit()
    db.refresh(symptom_entry)

    diagnosis = models.Diagnosis(
        symptom_entry_id=symptom_entry.id,
        diagnosis_text="This is a dummy diagnosis based on symptoms."
    )
    db.add(diagnosis)
    db.commit()
    db.refresh(symptom_entry)
    db.refresh(diagnosis)

    return symptom_entry

@router.get("/symptoms/{id}", response_model=SymptomEntryRead)
def get_symptom_entry(id: int, db: Session = Depends(getDB)):
    entry = db.query(models.SymptomEntry).filter(models.SymptomEntry.id == id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Symptom entry not found")
    return entry