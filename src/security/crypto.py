import json
import os
from functools import lru_cache

from cryptography.fernet import Fernet


@lru_cache(maxsize=1)
def _fernet() -> Fernet:
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        raise RuntimeError(
            "ENCRYPTION_KEY not set. Generate with: "
            "python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
        )
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt(plaintext: bytes) -> bytes:
    return _fernet().encrypt(plaintext)


def decrypt(ciphertext: bytes) -> bytes:
    return _fernet().decrypt(bytes(ciphertext))


def encrypt_json(obj) -> bytes:
    return encrypt(json.dumps(obj, separators=(",", ":")).encode("utf-8"))


def decrypt_json(blob: bytes) -> dict:
    return json.loads(decrypt(blob).decode("utf-8"))
