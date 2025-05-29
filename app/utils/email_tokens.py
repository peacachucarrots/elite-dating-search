"""
Helpers for signed URLs in e-mail confirmation / password reset, etc.
"""
from itsdangerous import URLSafeTimedSerializer
from flask import current_app as app


def _serializer(salt: str) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(
        app.config["SECRET_KEY"],
        salt=salt
    )


def generate_token(user_id: int, *, purpose: str, max_age: int = 86400) -> str:
    """Return a signed token that encodes the user id."""
    return _serializer(purpose).dumps(user_id)


def verify_token(token: str, *, purpose: str, max_age: int = 86400) -> int | None:
    """
    Return the user_id embedded in *token* or raise itsdangerous.BadSignature /
    SignatureExpired if invalid or too old.
    """
    try:
        return _serializer(purpose).loads(token, max_age=max_age)
    except Exception:
        return None
