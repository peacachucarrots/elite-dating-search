from app.models.program import ProgramApplication
from app.extensions import db

FIELD_LABELS = {
    "first_name":  "First name",
    "last_name":   "Last Name",
    "email":       "E-mail",
    "phone":       "Phone",
    "age":         "Age",
    "city":        "City",
    "state":       "State",
    "occupation":  "Occupation",
    "bio":         "About / bio",
    "photo":       "Photo file",
}

def latest_program_apps(limit: int = 50):
    """Return newest applications (client + candidate) as dicts."""
    rows = (
        ProgramApplication.query
        .order_by(ProgramApplication.submitted.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id":           r.id,
            "user_id":      r.user_id,
            "program":      r.program.value,
            "submitted":    r.submitted.isoformat(timespec="seconds"),
            "paid":         r.paid,
            "status":       r.status,
            **r.form_json,
        }
        for r in rows
    ]