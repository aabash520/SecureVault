"""Vault encryption utilities.

Secrets stored in the database are encrypted with AES-256-GCM using a key
derived from the user's master password + a per-user random salt (scrypt KDF).
The derived key lives only in the Flask session while the user is logged in;
logging out clears it, and the database alone cannot decrypt the vault.
"""
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

NONCE_SIZE = 12
KEY_SIZE = 32
SCRYPT_N = 2 ** 14
SCRYPT_R = 8
SCRYPT_P = 1


def new_salt() -> bytes:
    return os.urandom(16)


def derive_key(password: str, salt: bytes) -> bytes:
    kdf = Scrypt(salt=salt, length=KEY_SIZE, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P)
    return kdf.derive(password.encode("utf-8"))


def encrypt(key: bytes, plaintext: str) -> bytes:
    if plaintext is None:
        return None
    aes = AESGCM(key)
    nonce = os.urandom(NONCE_SIZE)
    ct = aes.encrypt(nonce, plaintext.encode("utf-8"), None)
    return nonce + ct


def decrypt(key: bytes, blob: bytes) -> str:
    if blob is None:
        return None
    aes = AESGCM(key)
    nonce, ct = blob[:NONCE_SIZE], blob[NONCE_SIZE:]
    return aes.decrypt(nonce, ct, None).decode("utf-8")


def password_strength(password: str) -> int:
    """Return a strength score 0-5 for the given password."""
    import re
    score = 0
    if len(password) >= 10:
        score += 1
    if len(password) >= 14:
        score += 1
    if re.search(r"[A-Z]", password) and re.search(r"[a-z]", password):
        score += 1
    if re.search(r"\d", password):
        score += 1
    if re.search(r"[^A-Za-z0-9]", password):
        score += 1
    return score
