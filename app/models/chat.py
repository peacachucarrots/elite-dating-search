# app/models/chat.py
from datetime import datetime
from sqlalchemy.sql import func

from ..extensions import db

class ChatSession(db.Model):
    __tablename__ = "chat_sessions"

    id          = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    socket_sid  = db.Column(db.String(32), unique=True)
    seq         = db.Column(db.Integer, nullable=False)
    opened_at   = db.Column(db.DateTime, default=datetime.utcnow)
    closed_at   = db.Column(db.DateTime, nullable=True)
    assigned_at = db.Column(db.DateTime)
    waiting_desc = db.Column(db.Boolean, nullable=False, default=True)
    replied_via_email = db.Column(db.Boolean, default=False)
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
    author  = db.Column(db.String(10), nullable=False)
    body    = db.Column(db.Text, nullable=False)
    ts      = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    chat_id = db.Column(db.Integer, db.ForeignKey("chat_sessions.id"), nullable=False)
    chat = db.relationship("ChatSession", back_populates="messages")

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user = db.relationship("User", back_populates="messages")
