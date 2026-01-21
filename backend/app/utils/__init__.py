"""
Cryptographic utilities for SSH key encryption.
"""

import base64
import secrets
from typing import Tuple

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def derive_key(password: str, salt: bytes) -> bytes:
    """
    Derive an encryption key from a password.
    
    Args:
        password: Master password
        salt: Random salt
        
    Returns:
        Derived key suitable for Fernet
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key


def encrypt_value(value: str, password: str) -> str:
    """
    Encrypt a value using a password.
    
    Args:
        value: Value to encrypt
        password: Encryption password
        
    Returns:
        Encrypted value as base64 string (salt + ciphertext)
    """
    salt = secrets.token_bytes(16)
    key = derive_key(password, salt)
    fernet = Fernet(key)
    
    encrypted = fernet.encrypt(value.encode())
    
    # Combine salt and encrypted data
    combined = salt + encrypted
    return base64.urlsafe_b64encode(combined).decode()


def decrypt_value(encrypted: str, password: str) -> str:
    """
    Decrypt a value using a password.
    
    Args:
        encrypted: Encrypted base64 string
        password: Encryption password
        
    Returns:
        Decrypted value
        
    Raises:
        InvalidToken: If decryption fails (wrong password)
    """
    combined = base64.urlsafe_b64decode(encrypted.encode())
    
    # Extract salt and ciphertext
    salt = combined[:16]
    ciphertext = combined[16:]
    
    key = derive_key(password, salt)
    fernet = Fernet(key)
    
    return fernet.decrypt(ciphertext).decode()


def generate_random_key() -> str:
    """Generate a random encryption key."""
    return secrets.token_urlsafe(32)
