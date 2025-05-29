# app/models/chat.py
import secrets
from datetime import datetime
from ..extensions import db

def _rand_id():
    return secrets.token_urlsafe(12)

class ChatSession(db.Model):
    __tablename__ = "chat_sessions"

    id          = db.Column(db.String(32), primary_key=True, default=_rand_id)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    seq         = db.Column(db.Integer, nullable=False)
    opened_at   = db.Column(db.DateTime, default=datetime.utcnow)
    closed_at   = db.Column(db.DateTime, nullable=True)
    assigned_at = db.Column(db.DateTime)
    rating      = db.Column(db.Integer)

    user        = db.relationship("User", back_populates="sessions")
    messages    = db.relationship(
                    "Message",
                    back_populates="chat",
                    cascade="all, delete-orphan",
                    lazy="dynamic",
    )

    @property
    def label(self) -> str:
        return f"{self.seq:04d}"


class Message(db.Model):
    __tablename__ = "messages"

    id      = db.Column(db.Integer, primary_key=True)
    author  = db.Column(db.String(8), nullable=False)
    body    = db.Column(db.Text, nullable=False)
    ts      = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    chat_id = db.Column(db.Integer, db.ForeignKey("chat_sessions.id"), nullable=False)
    chat = db.relationship("ChatSession", back_populates="messages")

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user = db.relationship("User", back_populates="messages")