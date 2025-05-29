# app/models/profile.py
from ..extensions import db

class Profile(db.Model):
    __tablename__ = "profiles"

    id      = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)

    first_name = db.Column(db.String(64))
    last_name  = db.Column(db.String(64))
    dob        = db.Column(db.Date)
    gender     = db.Column(
        db.Enum("male", "female", "nonbinary", "other", name="gender_enum")
    )

    user = db.relationship("User", back_populates="profile", uselist=False)