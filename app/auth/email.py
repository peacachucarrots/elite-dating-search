"""
app/auth/email.py
-----------------
Utility helpers for *transactional* e-mails:
  • account-verification (“confirm your e-mail”)
  • password-reset
Add more (welcome letter, TOTP setup, etc.) as you grow.
"""

from flask import current_app as app, render_template, url_for
from flask_mail import Message

from app.extensions import mail          # app/__init__.py sets this up
from app.models import User              # SQLAlchemy User model
from app.utils.email_tokens import generate_token, verify_token


# ------------------------------------------------------------------ #
# low-level helper                                                   #
# ------------------------------------------------------------------ #
def _send_email(subject: str, recipient: str,
                html_tpl: str, text_tpl: str, **ctx) -> None:
    """Render Jinja templates and send multipart e-mail."""
    html_body = render_template(html_tpl, **ctx)
    text_body = render_template(text_tpl, **ctx)

    msg = Message(
        subject     = subject,
        recipients  = [recipient],
        html        = html_body,
        body        = text_body,
        sender      = app.config.get("MAIL_DEFAULT_SENDER"),
    )
    mail.send(msg)


# ------------------------------------------------------------------ #
# public helpers                                                     #
# ------------------------------------------------------------------ #
def send_confirmation_email(user: User, confirm_url: str) -> None:
    _send_email(
        subject    ="Confirm your e-mail • Elite Dating Search",
        recipient  = user.email,
        html_tpl   ="auth/email/confirm.html",
        text_tpl   ="auth/email/confirm.txt",
        user       = user,
        confirm_url= confirm_url,
    )


def send_password_reset(user: User) -> None:
    token = generate_token(user.id, purpose="pw-reset")
    reset_url = url_for("auth.reset_password", token=token, _external=True)

    _send_email(
        subject   ="Reset your password • Elite Dating Search",
        recipient = user.email,
        html_tpl  ="auth/email/reset.html",
        text_tpl  ="auth/email/reset.txt",
        user      = user,
        reset_url = reset_url,
    )


# ------------------------------------------------------------------ #
# routes use these to redeem tokens                                  #
# ------------------------------------------------------------------ #
def confirm_email_token(token: str) -> User | None:
    uid = verify_token(token, purpose="email-confirm", max_age=86400)
    return User.query.get(uid) if uid else None


def verify_reset_token(token: str) -> User | None:
    uid = verify_token(token, purpose="pw-reset", max_age=3600)
    return User.query.get(uid) if uid else None