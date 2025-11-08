from pydantic import BaseModel
from typing import List, Optional

class DiagnosisCreate(BaseModel):
    symptom_entry_id: int
    diagnosis_text: str

class DiagnosisRead(BaseModel):
    id: int
    symptom_entry_id: int
    diagnosis_text: str
    class Config:
        orm_mode = True

class EntrySymptomRead(BaseModel):
    id: int
    symptom_id: Optional[int] = None    # FK to standard symptom, or None
    custom_symptom: Optional[str] = None
    class Config:
        orm_mode = True

class SymptomEntryRead(BaseModel):
    id: int
    submitted_at: str
    entry_symptoms: List[EntrySymptomRead]
    diagnosis: Optional[DiagnosisRead]
    class Config:
        orm_mode = True

class EntrySymptomCreate(BaseModel):
    symptom_id: Optional[int] = None
    custom_symptom: Optional[str] = None

class SymptomEntryCreate(BaseModel):
    symptoms: List[EntrySymptomCreate]