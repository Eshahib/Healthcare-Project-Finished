"""
Pydantic schemas for API request/response validation
"""
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime


class UserCreate(BaseModel):
    """Schema for creating a user."""
    username: str = Field(..., min_length=3, max_length=100)
    email: Optional[EmailStr] = None
    password: str = Field(..., min_length=6)


class UserResponse(BaseModel):
    """Schema for user response."""
    id: int
    username: str
    email: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schema for access token."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for token data."""
    username: Optional[str] = None


class SymptomEntryCreate(BaseModel):
    """Schema for creating a symptom entry."""
    symptoms: List[str] = Field(..., min_items=1, description="List of selected symptoms")
    comments: Optional[str] = Field(None, description="Patient's additional comments")
    user_id: Optional[int] = Field(None, description="User ID if authenticated")
    user_email: str = Field(None, description="User ID if authenticated")


class SymptomEntryResponse(BaseModel):
    """Schema for symptom entry response."""
    id: int
    user_id: Optional[int]
    symptoms: List[str]
    comments: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class DiagnosisCreate(BaseModel):
    """Schema for creating a diagnosis."""
    symptom_entry_id: int
    diagnosis_text: str
    confidence_score: Optional[str] = Field(None, description="high, medium, or low")
    possible_conditions: Optional[List[str]] = None
    recommendations: Optional[str] = None


class DiagnosisResponse(BaseModel):
    """Schema for diagnosis response."""
    id: int
    symptom_entry_id: int
    diagnosis_text: str
    confidence_score: Optional[str]
    possible_conditions: Optional[List[str]]
    recommendations: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class SymptomEntryWithDiagnosis(BaseModel):
    """Schema for symptom entry with diagnosis."""
    id: int
    user_id: Optional[int]
    symptoms: List[str]
    comments: Optional[str]
    created_at: datetime
    diagnosis: Optional[DiagnosisResponse] = None
    
    class Config:
        from_attributes = True

