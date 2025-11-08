# HIPAA-Compliant Symptom Checker Backend

## Overview
This backend implements HIPAA-compliant data handling with encryption at rest, audit logging, and secure API endpoints for a symptom checker application.

## Key Features

### ✅ Implemented
1. **PHI Encryption at Rest**: All sensitive data (symptoms, comments, diagnoses) is encrypted using AES-256-GCM
2. **Audit Logging**: All PHI access is logged to both files and database
3. **Secure API Endpoints**: RESTful API with proper error handling
4. **Data Validation**: Pydantic schemas for request/response validation
5. **Database Models**: Structured models with encrypted fields

### 🔄 For Production (Required)
1. **Cloud Key Management**: Move encryption keys to AWS KMS, Azure Key Vault, or Google Cloud KMS
2. **HIPAA-Compliant Cloud Storage**: Migrate to AWS HealthLake, Google Cloud Healthcare API, or Azure for Health
3. **Business Associate Agreement (BAA)**: Sign BAA with cloud provider
4. **HTTPS/TLS**: Enable SSL certificates for all API endpoints
5. **Authentication**: Implement user authentication and authorization
6. **Database Encryption**: Enable database encryption at rest
7. **Backup Encryption**: Encrypted backups with secure key management

## Installation

1. **Install Dependencies**:
```bash
cd Back_End
pip install -r requirements.txt
```

2. **Set Up Environment Variables**:
```bash
cp .env.example .env
# Edit .env with your database credentials and encryption key
```

3. **Generate Encryption Key** (for development):
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

4. **Run Database Migrations**:
```bash
python main.py
# This will create all database tables
```

5. **Start the Server**:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### POST `/api/symptoms`
Create a new symptom entry with encrypted PHI storage.

**Request Body**:
```json
{
  "symptoms": ["Fever", "Cough", "Headache"],
  "comments": "Started 3 days ago, getting worse",
  "user_id": 1
}
```

**Response**:
```json
{
  "id": 1,
  "user_id": 1,
  "symptoms": ["Fever", "Cough", "Headache"],
  "comments": "Started 3 days ago, getting worse",
  "created_at": "2025-01-20T10:00:00Z"
}
```

### GET `/api/symptoms/{symptom_id}`
Get a symptom entry by ID (with diagnosis if available).

### POST `/api/diagnoses`
Create a diagnosis for a symptom entry.

**Request Body**:
```json
{
  "symptom_entry_id": 1,
  "diagnosis_text": "Based on symptoms, possible common cold...",
  "confidence_score": "medium",
  "possible_conditions": ["Common Cold", "Flu"],
  "recommendations": "Rest, stay hydrated, monitor symptoms"
}
```

## Data Storage

### What We Save:
1. **Symptoms**: Array of selected symptoms (encrypted)
2. **Comments**: Patient's additional notes (encrypted)
3. **Diagnosis**: LLM analysis results (encrypted)
4. **Metadata**: Timestamps, user IDs, confidence scores (non-PHI)
5. **Audit Logs**: All PHI access records

### Encryption:
- Symptoms list: Encrypted as JSON string
- Patient comments: Encrypted text
- Diagnosis text: Encrypted text
- Recommendations: Encrypted text

### Audit Logging:
- User ID
- Action (CREATE, READ, UPDATE, DELETE)
- Resource type and ID
- IP address
- User agent
- Timestamp
- Success/failure status

## Security Considerations

### Current Implementation:
- ✅ Encryption at rest for all PHI
- ✅ Audit logging for PHI access
- ✅ Data validation with Pydantic
- ✅ Secure error handling
- ✅ CORS configuration

### Production Requirements:
- ⚠️ Move encryption keys to cloud KMS
- ⚠️ Use HTTPS/TLS for all communications
- ⚠️ Implement user authentication
- ⚠️ Enable database encryption
- ⚠️ Set up monitoring and alerting
- ⚠️ Regular security audits
- ⚠️ Backup encryption
- ⚠️ Disaster recovery plan

## Cloud Migration Guide

See `HIPAA_COMPLIANCE.md` for detailed cloud migration instructions for:
- AWS HealthLake
- Google Cloud Healthcare API
- Azure for Health

## Testing

```bash
# Test health endpoint
curl http://localhost:8000/health

# Create symptom entry
curl -X POST http://localhost:8000/api/symptoms \
  -H "Content-Type: application/json" \
  -d '{
    "symptoms": ["Fever", "Cough"],
    "comments": "Started yesterday"
  }'
```

## Compliance Checklist

See `HIPAA_COMPLIANCE.md` for the complete compliance checklist.

## Support

For questions about HIPAA compliance, consult your organization's compliance officer or legal team.

