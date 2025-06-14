"""
Helpers for signed URLs in e-mail confirmation / password reset, etc.
"""
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired, BadTimeSignature
from flask import url_for, current_app as app
from flask_mail import Mail, Message
from app.settings import Base

SUPPORT_INBOX = "clientrelations@elitedatingsearch.com"

def send_support_email(name: str, subject: str | None, sender: str, message: str) -> None:
    from app.extensions import mail
    subj = f"[Contact Form] {subject.strip() if subject else 'No subject'}"

    body = (
        f"Name: {name}\n"
        f"Email: {sender}\n\n"
        f"Message:\n{message}\n"
    )

    msg = Message(
        subject=subj,
        recipients=[SUPPORT_INBOX],
        body=message,
        reply_to=sender,
        sender=app.config["MAIL_DEFAULT_SENDER"]
    )

    mail.send(msg)

def _serializer(salt: str) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(
        app.config["SECRET_KEY"],
        salt=salt
    )

def generate_confirmation_url(user):
    s = _serializer("email-confirm")
    token = s.dumps(user.id)
    return url_for("auth.confirm_email", token=token, _external=True)

def generate_token(user_id: int, *, purpose: str, max_age: int = 86400) -> str:
    """Return a signed token that encodes the user id."""
    return _serializer(purpose).dumps(user_id)


def verify_token(token: str, *, purpose: str, max_age: int = 86400) -> int | None:
    """
    Return the user_id embedded in *token* or raise itsdangerous.BadSignature /
    SignatureExpired if invalid or too old.
    """
    s = _serializer(purpose)
    try:
        return s.loads(token, max_age=max_age)
    except SignatureExpired:
        app.logger.warning("Token expired")
    except (BadSignature, BadTimeSignature):
        app.logger.warning("Bad signature")
    return None
