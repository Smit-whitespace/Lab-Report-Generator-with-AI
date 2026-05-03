import base64
import hashlib
import hmac
import json
import secrets
import time

from app.core.config import SECRET_KEY


PASSWORD_ITERATIONS = 120_000
TOKEN_EXPIRE_SECONDS = 8 * 60 * 60


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PASSWORD_ITERATIONS,
    ).hex()

    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt}${password_hash}"


def verify_password(password: str, stored_password_hash: str) -> bool:
    try:
        algorithm, iterations, salt, password_hash = stored_password_hash.split("$")
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    incoming_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        int(iterations),
    ).hex()

    return secrets.compare_digest(incoming_hash, password_hash)


def _base64_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("utf-8")


def _base64_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def create_access_token(user_id: int, role: str) -> str:
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": int(time.time()) + TOKEN_EXPIRE_SECONDS,
    }
    body = _base64_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(
        SECRET_KEY.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256,
    ).digest()

    return f"{body}.{_base64_encode(signature)}"


def decode_access_token(token: str) -> dict | None:
    try:
        body, signature = token.split(".")
    except ValueError:
        return None

    expected_signature = hmac.new(
        SECRET_KEY.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256,
    ).digest()

    if not hmac.compare_digest(_base64_encode(expected_signature), signature):
        return None

    try:
        payload = json.loads(_base64_decode(body))
    except (json.JSONDecodeError, ValueError):
        return None

    if payload.get("exp", 0) < int(time.time()):
        return None

    return payload
