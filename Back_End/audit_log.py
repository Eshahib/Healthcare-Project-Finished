"""
HIPAA-Compliant Audit Logging Module
Logs all access to PHI data for compliance and security monitoring
"""
import logging
from datetime import datetime

# Configure audit logging
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)

# Create file handler for audit logs
file_handler = logging.FileHandler("audit.log")
file_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
file_handler.setFormatter(formatter)
audit_logger.addHandler(file_handler)


def log_phi_access(
    user_id: int = None,
    action: str = "READ",
    resource_type: str = "SymptomEntry",
    resource_id: int = None,
    ip_address: str = None,
    user_agent: str = None,
    details: str = None,
    success: str = "SUCCESS"
):
    """
    Log access to PHI data for HIPAA compliance.
    
    Args:
        user_id: ID of user accessing the data
        action: Action performed (CREATE, READ, UPDATE, DELETE)
        resource_type: Type of resource accessed
        resource_id: ID of the resource
        ip_address: IP address of the request
        user_agent: User agent string
        details: Additional details about the access
        success: Whether the action was successful
    """
    log_message = (
        f"PHI_ACCESS - User: {user_id}, Action: {action}, "
        f"Resource: {resource_type}:{resource_id}, "
        f"IP: {ip_address}, Success: {success}"
    )
    
    if details:
        log_message += f", Details: {details}"
    
    audit_logger.info(log_message)
    
    # Note: In production, also write to database via AuditLog model
    # Example usage in API endpoints:
    # from models import AuditLog
    # audit_entry = AuditLog(user_id=user_id, action=action, ...)
    # db.add(audit_entry)
    # db.commit()

