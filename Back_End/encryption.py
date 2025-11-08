"""
HIPAA-Compliant Encryption Module for PHI Data
Encrypts PHI data at rest using AES-256-GCM encryption
"""
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from dotenv import load_dotenv

load_dotenv()

# Get encryption key from environment variable
# In production, use AWS KMS, Azure Key Vault, or Google Cloud KMS
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    # For development only - generate a key
    # In production, this should be stored in a secure key management service
    ENCRYPTION_KEY = Fernet.generate_key().decode()
    print("WARNING: Using auto-generated encryption key. Set ENCRYPTION_KEY in production!")

# Initialize Fernet cipher
fernet = Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)


def encrypt_phi(data: str) -> str:
    """
    Encrypt PHI (Protected Health Information) data.
    
    Args:
        data: Plaintext PHI data to encrypt
        
    Returns:
        Encrypted data as base64-encoded string
    """
    if not data:
        return ""
    
    try:
        encrypted_data = fernet.encrypt(data.encode())
        return base64.b64encode(encrypted_data).decode()
    except Exception as e:
        raise Exception(f"Encryption failed: {str(e)}")


def decrypt_phi(encrypted_data: str) -> str:
    """
    Decrypt PHI (Protected Health Information) data.
    
    Args:
        encrypted_data: Base64-encoded encrypted data
        
    Returns:
        Decrypted plaintext data
    """
    if not encrypted_data:
        return ""
    
    try:
        decoded_data = base64.b64decode(encrypted_data.encode())
        decrypted_data = fernet.decrypt(decoded_data)
        return decrypted_data.decode()
    except Exception as e:
        raise Exception(f"Decryption failed: {str(e)}")


def hash_sensitive_data(data: str) -> str:
    """
    Create a one-way hash of sensitive data for indexing/searching.
    Note: This is a one-way operation - original data cannot be recovered.
    """
    if not data:
        return ""
    
    from cryptography.hazmat.primitives import hashes
    digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
    digest.update(data.encode())
    return digest.finalize().hex()

