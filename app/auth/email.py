"""
app/auth/email.py
-----------------
Utility helpers for *transactional* e-mails:
  • account-verification (“confirm your e-mail”)
  • password-reset
Add more (welcome letter, TOTP setup, etc.) as you grow.
"""

from flask import current_app, render_template, url_for
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer

from app.extensions import mail          # app/__init__.py sets this up
from app.models import User              # SQLAlchemy User model


# --------------------------------------------------------------------------- #
# Internals                                                                   #
# --------------------------------------------------------------------------- #
def _generate_token(email: str, purpose: str, expires_in: int = 3600) -> str:
    """
    Return a time-limited signed token for *email* and *purpose*.
    - purpose: "verify"  |  "reset"
    """
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return s.dumps({"email": email, "purpose": purpose},
                   salt=f"auth-{purpose}")


def _verify_token(token: str, purpose: str, max_age: int = 3600) -> str | None:
    """Return e-mail stored in *token* if valid / within *max_age* seconds."""
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        data = s.loads(token, max_age=max_age, salt=f"auth-{purpose}")
        if data.get("purpose") == purpose:
            return data["email"]
    except Exception:
        pass
    return None


def _send_email(subject: str,
                recipient: str,
                html_tpl: str,
                text_tpl: str,
                **ctx) -> None:
    """
    Render *html_tpl* / *text_tpl* with **ctx and send a multipart e-mail.
    Template path is relative to *app/templates/*.
    """
    html_body = render_template(html_tpl, **ctx)
    text_body = render_template(text_tpl, **ctx)

    msg = Message(subject,
                  recipients=[recipient],
                  html=html_body,
                  body=text_body)
    mail.send(msg)  # hand off to background worker later, if desired


# --------------------------------------------------------------------------- #
# Public helpers                                                              #
# --------------------------------------------------------------------------- #
def send_confirmation(user: User) -> None:
    """Send a ‘confirm your address’ link to *user*."""
    token = _generate_token(user.email, purpose="verify")
    confirm_url = url_for("auth.confirm_email", token=token, _external=True)

    _send_email(
        subject="Confirm your e-mail • Elite Dating Search",
        recipient=user.email,
        html_tpl="auth/email/confirm.html",
        text_tpl="auth/email/confirm.txt",
        user=user,
        confirm_url=confirm_url,
    )


def send_password_reset(user: User) -> None:
    """Send a ‘reset your password’ link to *user*."""
    token = _generate_token(user.email, purpose="reset")
    reset_url = url_for("auth.reset_password", token=token, _external=True)

    _send_email(
        subject="Reset your password • Elite Dating Search",
        recipient=user.email,
        html_tpl="auth/email/reset.html",
        text_tpl="auth/email/reset.txt",
        user=user,
        reset_url=reset_url,
    )


# --------------------------------------------------------------------------- #
# Token-validation helpers used by routes                                     #
# --------------------------------------------------------------------------- #
def confirm_email_token(token: str) -> User | None:
    """
    Validate *token* for e-mail verification.
    Return matching User or None.
    """
    if (email := _verify_token(token, purpose="verify")):
        return User.query.filter_by(email=email).first()
    return None


def verify_reset_token(token: str) -> User | None:
    """
    Validate *token* for password reset.
    Return matching User or None.
    """
    if (email := _verify_token(token, purpose="reset")):
        return User.query.filter_by(email=email).first()
    return None