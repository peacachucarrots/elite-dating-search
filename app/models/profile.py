# app/models/profile.py
from datetime import date
from ..extensions import db

class Profile(db.Model):
    __tablename__ = "profiles"

    id      = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)

    first_name = db.Column(db.String(64))
    last_name  = db.Column(db.String(64))
    display_name = db.Column(db.String(80))
    dob        = db.Column(db.Date)
    gender     = db.Column(
        db.Enum("male", "female", "nonbinary", "other", name="gender_enum")
    )

    user = db.relationship("User", back_populates="profile", uselist=False)

    @property
    def age(self) -> int | None:
        """Return the user’s age in whole years (or None if DOB missing)."""
        if not self.dob:
            return None
        today = date.today()
        before_birthday = (today.month, today.day) < (self.dob.month, self.dob.day)
        return today.year - self.dob.year - int(before_birthday)