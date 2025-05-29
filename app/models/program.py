# app/models/program.py
from datetime import datetime

from ..extensions import db

class ProgramApplication(db.Model):
    __tablename__ = "program_applications"

    id        = db.Column(db.Integer, primary_key=True)

    # ── ownership ──────────────────────────────────────────────────
    user_id   = db.Column(db.Integer,
                          db.ForeignKey("users.id", ondelete="CASCADE"),
                          nullable=False)
    user      = db.relationship("User", back_populates="applications")

    # ── program metadata ──────────────────────────────────────────
    program   = db.Column(db.Enum("client", "candidate",
                                  name="program_enum"),
                          nullable=False)
    submitted = db.Column(db.DateTime, default=datetime.utcnow)

    # ── contact / profile details (optional) ──────────────────────
    street          = db.Column(db.String(128))
    city            = db.Column(db.String(64))
    state           = db.Column(db.String(32))
    zip             = db.Column(db.String(16))
    country         = db.Column(db.String(64))

    occupation      = db.Column(db.String(64))
    income_bracket  = db.Column(db.String(32))   # “100-250 K”, “500 K+” …
    education       = db.Column(db.String(32))   # “Bachelor”, “MBA”, …
    marital_status  = db.Column(db.String(16))   # “single”, “divorced” …
    ref_src         = db.Column(db.String(32))   # marketing attribution
    intro           = db.Column(db.Text)         # free-text self-summary

    # ── paid-client specifics ─────────────────────────────────────
    fee_paid   = db.Column(db.Boolean, default=False)
    stripe_pi  = db.Column(db.String(64))        # PaymentIntent ID

    def __repr__(self) -> str:                   # nice debug print
        return f"<App {self.id} {self.program} for user {self.user_id}>"