"""
app/auth/email.py
-----------------
Utility helpers for *transactional* e-mails:
  • account-verification (“confirm your e-mail”)
  • password-reset
Add more (welcome letter, TOTP setup, etc.) as you grow.
"""

from flask import render_template, url_for
from app.models import User
from app.utils.email_tokens import generate_token, verify_token

import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv

load_dotenv()

# ------------------------------------------------------------------ #
# low-level helper                                                   #
# ------------------------------------------------------------------ #
def _send_email(subject: str, recipient: str,
                html_tpl: str, text_tpl: str, **ctx) -> None:
    """Send Email via SendGrid API."""
    html_body = render_template(html_tpl, **ctx)
    text_body = render_template(text_tpl, **ctx)

    message = Mail(
        from_email=os.environ.get("MAIL_USERNAME"),
        to_emails=recipient,
        subject=subject,
        plain_text_content=text_body,
        html_content=html_body)
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        if hasattr(e, "status_code"):
            print("Status:", e.status_code)
        if hasattr(e, "body"):
            print("Body:", e.body)


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