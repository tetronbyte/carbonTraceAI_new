"""Secure credential storage with Fernet encryption."""
import os
import json
from cryptography.fernet import Fernet
from typing import Dict, Any

# Generate key with: Fernet.generate_key()
# Store in environment: CREDENTIAL_ENCRYPTION_KEY
FERNET_KEY = os.getenv("CREDENTIAL_ENCRYPTION_KEY", Fernet.generate_key().decode())
cipher = Fernet(FERNET_KEY.encode() if isinstance(FERNET_KEY, str) else FERNET_KEY)


class CredentialManager:
    """Manages encryption/decryption of ERP credentials."""
    
    @staticmethod
    def encrypt_credentials(creds: Dict[str, Any]) -> str:
        """Encrypt credentials dictionary to string."""
        raw = json.dumps(creds).encode()
        encrypted = cipher.encrypt(raw)
        return encrypted.decode()
    
    @staticmethod
    def decrypt_credentials(encrypted: str) -> Dict[str, Any]:
        """Decrypt credentials string to dictionary."""
        decrypted = cipher.decrypt(encrypted.encode())
        return json.loads(decrypted)
