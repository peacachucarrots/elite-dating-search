"""
Configuration objects.
"""

from pathlib import Path
import os
from datetime import time
from zoneinfo import ZoneInfo

EASTERN = ZoneInfo("America/New_York")

OFFICE_OPEN  = time(9, 0)
OFFICE_CLOSE = time(18, 0)

BASE_DIR = Path(__file__).resolve().parent.parent


# --------------------------------------------------------------------------- #
# Common / base                                                               #
# --------------------------------------------------------------------------- #
class Base:
    """Settings shared by all environments."""
    # ── Core ────────────────────────────────────────────────────────────────
    SECRET_KEY                 = os.environ.get("SECRET_KEY")
    SESSION_COOKIE_HTTPONLY    = True
    SESSION_COOKIE_SAMESITE    = "Lax"
    SEND_FILE_MAX_AGE_DEFAULT  = 60 * 60

    # ── Flask Rate-Limiter ───────────────────────────────────────────────────
    RATELIMIT_DEFAULT = "10/minute"

    # ── Flask-SQLAlchemy ───────────────────────────────────────────────────
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── Mail (Flask-Mail) ────────────────────────────────────
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = os.environ.get("MAIL_PORT")
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS")
    MAIL_USE_SSL = os.environ.get("MAIL_USE_SSL")
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER")

    # ── 2FA / TOTP ─────────────────────────────────────────────────────────
    SECURITY_2FA_SECRET = os.environ.get("TOTP_SECRET", "totp-seed-dev")
    TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
    TWILIO_FROM_NUMBER = os.environ.get("TWILIO_FROM_NUMBER")

    # ── OAuth (google-auth-flask) ──────────────────────────────────────────
    OAUTHLIB_INSECURE_TRANSPORT = os.environ.get("OAUTHLIB_INSECURE_TRANSPORT", "0")
    GOOGLE_CLIENT_ID     = os.environ.get("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")


# --------------------------------------------------------------------------- #
# Development                                                                 #
# --------------------------------------------------------------------------- #
class Dev(Base):
    DEBUG  = True
    TESTING = False

    SOCKETIO_ASYNC_MODE = os.environ.get("SOCKETIO_ASYNC_MODE")
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI")
    SQLALCHEMY_ECHO = True


# --------------------------------------------------------------------------- #
# Pytest / CI                                                                 #
# --------------------------------------------------------------------------- #
class Test(Base):
    TESTING = True
    DEBUG   = False

    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SOCKETIO_MESSAGE_QUEUE = None


# --------------------------------------------------------------------------- #
# Production                                                                  #
# --------------------------------------------------------------------------- #
class Prod(Base):
    DEBUG   = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME = "https"

    # ── Flask-SocketIO ──────────────────────────────
    SOCKETIO_MESSAGE_QUEUE = os.environ.get("SOCKETIO_MESSAGE_QUEUE")
    SOCKETIO_ASYNC_MODE = os.environ.get("SOCKETIO_ASYNC_MODE")

    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI")

