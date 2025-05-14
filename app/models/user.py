# app/models/user.py
from __future__ import annotations

from datetime import datetime

from argon2 import PasswordHasher, exceptions as argon_exc
from flask_login import UserMixin
from sqlalchemy.orm import validates

from app.extensions import db    # ← the SQLAlchemy() instance created in extensions.py

# ── password hasher (Argon2id) ───────────────────────────────────────────────
ph = PasswordHasher(
    time_cost=2,     # iterations
    memory_cost=102_400,  # KiB
    parallelism=8,
)

# ── model ─────────────────────────────────────────────────────────────────────
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id          = db.Column(db.Integer, primary_key=True)
    email       = db.Column(db.String(255), unique=True, nullable=False, index=True)
    pw_hash     = db.Column(db.String(255), nullable=False)
    is_active   = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    last_login  = db.Column(db.DateTime)

    # ── password helpers ──────────────────────────────────────────────────
    def set_password(self, raw: str) -> None:
        """Hash & store the user’s password."""
        self.pw_hash = ph.hash(raw)

    def check_password(self, raw: str) -> bool:
        """Verify a raw password against the stored hash."""
        try:
            return ph.verify(self.pw_hash, raw)
        except argon_exc.VerifyMismatchError:
            return False

    # ── normalise / validate fields ───────────────────────────────────────
    @validates("email")
    def _lowercase_email(self, _, value: str) -> str:
        return value.strip().lower()

    # ── nice repr for debugging ───────────────────────────────────────────
    def __repr__(self) -> str:  # pragma: no cover
        return f"<User {self.id} {self.email}>"