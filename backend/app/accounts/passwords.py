"""Salted scrypt passwords using Python's OpenSSL-backed implementation."""

from hashlib import scrypt
from secrets import compare_digest, token_bytes
from threading import BoundedSemaphore

# OWASP's n=2^17, r=8, p=1 configuration; at most two 128MiB hashes concurrently.
_hash_slots = BoundedSemaphore(2)
DUMMY_PASSWORD_HASH = "scrypt-v1$" + "00" * 16 + "$" + "00" * 64


def _derive(password: str, salt: bytes) -> bytes:
    with _hash_slots:
        return scrypt(
            password.encode("utf-8"), salt=salt, n=131072, r=8, p=1,
            maxmem=256 * 1024 * 1024, dklen=64,
        )


def hash_password(password: str) -> str:
    salt = token_bytes(16)
    return f"scrypt-v1${salt.hex()}${_derive(password, salt).hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        version, salt_hex, expected_hex = stored.split("$")
        salt, expected = bytes.fromhex(salt_hex), bytes.fromhex(expected_hex)
        if version != "scrypt-v1" or len(salt) != 16 or len(expected) != 64:
            return False
        return compare_digest(_derive(password, salt), expected)
    except (ValueError, TypeError):
        return False
