"""
Configuration objects.

Usage
-----
>>> app = Flask(__name__)
>>> app.config.from_object("app.settings.Dev")  # or Prod / Test
"""

from pathlib import Path
import os
from datetime import time
from zoneinfo import ZoneInfo

EASTERN = ZoneInfo("America/New_York")

OFFICE_OPEN  = time(9, 0)   # 09:00
OFFICE_CLOSE = time(18, 0)  # 18:00

BASE_DIR = Path(__file__).resolve().parent.parent


# --------------------------------------------------------------------------- #
# Common / base                                                               #
# --------------------------------------------------------------------------- #
class Base:
    """Settings shared by all environments."""
    # ── Core ────────────────────────────────────────────────────────────────
    SECRET_KEY                 = os.environ.get("SECRET_KEY", "dev-change-me")
    SESSION_COOKIE_HTTPONLY    = True
    SESSION_COOKIE_SAMESITE    = "Lax"
    SEND_FILE_MAX_AGE_DEFAULT  = 60 * 60          # 1 hour (static-file cache bust)

    # ── Flask-SQLAlchemy ───────────────────────────────────────────────────
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── Flask-SocketIO (optional Redis queue) ──────────────────────────────
    SOCKETIO_MESSAGE_QUEUE     = os.environ.get("REDIS_URL")  # e.g. redis://localhost:6379/0

    # ── Mail (Flask-Mail or Flask-SMTP) ────────────────────────────────────
    MAIL_SERVER = "smtp.zoho.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = "no-reply@elitedatingsearch.com"
    MAIL_PASSWORD = "95TWEYdJqUkQ"
    MAIL_DEFAULT_SENDER = ("Elite Dating Search", "no-reply@elitedatingsearch.com")

    # ── 2FA / TOTP ─────────────────────────────────────────────────────────
    SECURITY_2FA_SECRET = os.environ.get("TOTP_SECRET", "totp-seed-dev")
    TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
    TWILIO_FROM_NUMBER = os.environ.get("TWILIO_FROM_NUMBER")

    # ── OAuth (google-auth-flask) ──────────────────────────────────────────
    OAUTHLIB_INSECURE_TRANSPORT = os.environ.get("OAUTHLIB_INSECURE_TRANSPORT", "0")
    GOOGLE_CLIENT_ID     = os.environ.get("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")

    # Extend/override freely in subclasses …


# --------------------------------------------------------------------------- #
# Development                                                                 #
# --------------------------------------------------------------------------- #
class Dev(Base):
    DEBUG  = True
    TESTING = False

    # Local SQLite db (file sits next to repo root)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DEV_DATABASE_URI",
        f"sqlite:///{BASE_DIR / 'dev.db'}"
    )

    # Echo SQL statements to console for easier debugging
    SQLALCHEMY_ECHO = True


# --------------------------------------------------------------------------- #
# Pytest / CI                                                                 #
# --------------------------------------------------------------------------- #
class Test(Base):
    TESTING = True
    DEBUG   = False

    # In-memory SQLite speeds up the test-suite
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

    # Disable Redis during tests unless you’re explicitly covering socket-logic
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

    # Make sure you really give Flask a strong secret key in prod!