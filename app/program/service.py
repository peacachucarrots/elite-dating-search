from app.models.program import ProgramApplication
from app.extensions import db

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
            "program":      r.program.value,      # "client" / "candidate"
            "submitted":    r.submitted.isoformat(timespec="seconds"),
            "paid":         r.paid,
            "status":       r.status,
            **r.form_json,                       # flatten answers
        }
        for r in rows
    ]