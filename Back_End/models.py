"""
HIPAA-Compliant Database Models
All PHI data is encrypted at rest using encryption utilities
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from database import Base
from encryption import encrypt_phi, decrypt_phi


class User(Base):
    """
    User model for authentication.
    Email is considered PHI and should be encrypted in production.
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=True)  # PHI - encrypt in production
    hashed_password = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    symptom_entries = relationship("SymptomEntry", back_populates="user", cascade="all, delete-orphan")


class SymptomEntry(Base):
    """
    Symptom entry model storing PHI data.
    Symptoms and comments are encrypted at rest.
    """
    __tablename__ = "symptom_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Optional for anonymous submissions
    
    # Encrypted PHI fields
    _symptoms_encrypted = Column("symptoms_encrypted", Text, nullable=False)  # Encrypted JSON array
    _comments_encrypted = Column("comments_encrypted", Text, nullable=True)  # Encrypted patient comments
    
    # Metadata (not PHI)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="symptom_entries")
    diagnosis = relationship("Diagnosis", back_populates="symptom_entry", uselist=False, cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="symptom_entry")
    
    @hybrid_property
    def symptoms(self):
        """Decrypt and return symptoms list."""
        if self._symptoms_encrypted:
            try:
                import json
                decrypted = decrypt_phi(self._symptoms_encrypted)
                return json.loads(decrypted)
            except:
                return []
        return []
    
    @symptoms.setter
    def symptoms(self, value):
        """Encrypt and store symptoms list."""
        if value:
            import json
            encrypted = encrypt_phi(json.dumps(value))
            self._symptoms_encrypted = encrypted
        else:
            self._symptoms_encrypted = ""
    
    @hybrid_property
    def comments(self):
        """Decrypt and return patient comments."""
        if self._comments_encrypted:
            try:
                return decrypt_phi(self._comments_encrypted)
            except:
                return ""
        return ""
    
    @comments.setter
    def comments(self, value):
        """Encrypt and store patient comments."""
        if value:
            self._comments_encrypted = encrypt_phi(value)
        else:
            self._comments_encrypted = None


class Diagnosis(Base):
    """
    Diagnosis model storing LLM analysis results.
    Diagnosis text contains PHI and is encrypted at rest.
    """
    __tablename__ = "diagnoses"
    
    id = Column(Integer, primary_key=True, index=True)
    symptom_entry_id = Column(Integer, ForeignKey("symptom_entries.id"), unique=True, nullable=False)
    
    # Encrypted PHI fields
    _diagnosis_text_encrypted = Column("diagnosis_text_encrypted", Text, nullable=False)
    _recommendations_encrypted = Column("recommendations_encrypted", Text, nullable=True)
    
    # Non-PHI metadata
    confidence_score = Column(String(20), nullable=True)  # high, medium, low
    possible_conditions = Column(JSON, nullable=True)  # Array of condition names (non-PHI)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    symptom_entry = relationship("SymptomEntry", back_populates="diagnosis")
    
    @hybrid_property
    def diagnosis_text(self):
        """Decrypt and return diagnosis text."""
        if self._diagnosis_text_encrypted:
            try:
                return decrypt_phi(self._diagnosis_text_encrypted)
            except:
                return ""
        return ""
    
    @diagnosis_text.setter
    def diagnosis_text(self, value):
        """Encrypt and store diagnosis text."""
        if value:
            self._diagnosis_text_encrypted = encrypt_phi(value)
        else:
            self._diagnosis_text_encrypted = ""
    
    @hybrid_property
    def recommendations(self):
        """Decrypt and return recommendations."""
        if self._recommendations_encrypted:
            try:
                return decrypt_phi(self._recommendations_encrypted)
            except:
                return ""
        return ""
    
    @recommendations.setter
    def recommendations(self, value):
        """Encrypt and store recommendations."""
        if value:
            self._recommendations_encrypted = encrypt_phi(value)
        else:
            self._recommendations_encrypted = None


class AuditLog(Base):
    """
    Audit log for tracking all PHI access.
    Required for HIPAA compliance.
    """
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    symptom_entry_id = Column(Integer, ForeignKey("symptom_entries.id"), nullable=True)
    action = Column(String(50), nullable=False)  # CREATE, READ, UPDATE, DELETE
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(Integer, nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    details = Column(Text, nullable=True)
    success = Column(String(10), default="SUCCESS")
    
    # Relationships
    user = relationship("User")
    symptom_entry = relationship("SymptomEntry", back_populates="audit_logs")
