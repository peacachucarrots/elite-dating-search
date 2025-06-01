# app/models/user.py
from __future__ import annotations

from datetime import datetime

from argon2 import PasswordHasher, exceptions as argon_exc
from flask_login import UserMixin
from sqlalchemy.orm import validates

from .profile import Profile
from .role import user_roles
from ..extensions import db

# ── password hasher (Argon2id) ───────────────────────────────────────────────
ph = PasswordHasher(
    time_cost=2,        # iterations
    memory_cost=102_400,  # ~100 MB RAM
    parallelism=8,
    hash_len=32,
    salt_len=16,
)

# ── model ─────────────────────────────────────────────────────────────────────
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id          = db.Column(db.Integer, primary_key=True)
    email       = db.Column(db.String(255), unique=False, index=True, nullable=False)
    pw_hash     = db.Column(db.String(255), nullable=False)

    phone             = db.Column(db.String(20), unique=False)
    phone_otp         = db.Column(db.String(6))
    phone_otp_sent    = db.Column(db.DateTime)
    is_phone_verified = db.Column(db.Boolean, default=False)

    is_active   = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)

    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    last_login  = db.Column(db.DateTime)

    profile = db.relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    @property
    def display_name(self) -> str:
        p = self.profile
        if p:
            if p.display_name:
                return p.display_name
            if p.first_name and p.last_name:
                return f"{p.first_name} {p.last_name}"
        return self.email.split("@")[0]

    roles = db.relationship("Role", secondary=user_roles, lazy="joined")
    sessions = db.relationship("ChatSession", back_populates="user")

    messages = db.relationship(
        "Message",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    applications = db.relationship(
        "ProgramApplication",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    # ── Flask-Login hook ───────────────────────────────────────────────────
    def get_id(self) -> str:  # type: ignore[override]
        return str(self.id)

    # ── Role Helper functions ───────────────────────────────────────────────────
    def has_role(self, name: str) -> bool:
        return any(r.name == name for r in self.roles)

    def max_role_level(self) -> int:
        return max((r.level for r in self.roles), default=0)

    def is_rep(user):
        return user.max_role_level() >= 20

    def is_admin(user):
        return user.max_role_level() >= 30

    # ── Password helpers (Argon-2) ─────────────────────────────────────────
    # called from auth.routes.register()
    @staticmethod
    def hash_password(raw: str) -> str:
        """Return Argon-2 hash for *raw*."""
        return ph.hash(raw)

    def check_password(self, raw: str) -> bool:
        """
        Verify *raw* against stored hash.
        If parameters were strengthened, transparently re-hash & save.
        """
        try:
            valid = ph.verify(self.pw_hash, raw)
        except argon_exc.VerifyMismatchError:
            return False

        # Re-hash if our policy got stronger since this hash was generated
        if ph.check_needs_rehash(self.pw_hash):
            self.pw_hash = ph.hash(raw)
            db.session.commit()

        return valid

    # ── Normalize e-mail ──────────────────────────────────────────────────
    @validates("email")
    def _normalize_email(self, _, value: str) -> str:
        return value.strip().lower()

    # ── nice repr for debugging ───────────────────────────────────────────
    def __repr__(self) -> str:  # pragma: no cover
        return f"<User {self.id} {self.email}>"