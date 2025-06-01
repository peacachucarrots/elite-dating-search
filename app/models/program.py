# app/models/program.py
import enum
from datetime import datetime
from ..extensions import db

class ProgramType(enum.Enum):
    CLIENT    = "client"
    CANDIDATE = "candidate"

class ProgramApplication(db.Model):
    __tablename__ = "program_applications"

    id        = db.Column(db.Integer, primary_key=True)

    # ── ownership ──────────────────────────────────────────────────
    user_id   = db.Column(db.Integer,
                          db.ForeignKey("users.id", ondelete="CASCADE"),
                          nullable=False)
    user      = db.relationship("User", back_populates="applications")

    # ── program metadata ──────────────────────────────────────────
    program   = db.Column(db.Enum(ProgramType), nullable=False)
    submitted = db.Column(db.DateTime, default=datetime.utcnow)

    # ── paid-client specifics ─────────────────────────────────────
    status = db.Column(db.String(24), default="new")
    ach_signed = db.Column(db.Boolean, default=False, nullable=False)
    ach_doc_url = db.Column(db.String(255))  # e.g. DocuSign envelope URL
    paid = db.Column(db.Boolean, default=False, nullable=False)

    form_json = db.Column(db.JSON, nullable=False)

    def __repr__(self) -> str:                   # nice debug print
        return f"<App {self.id} {self.program} for user {self.user_id}>"