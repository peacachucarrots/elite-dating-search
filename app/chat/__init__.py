# app/chat/__init__.py
from flask import Blueprint

bp = Blueprint(
    "chat",
    __name__,
    template_folder="templates",   # where rep.html lives
    static_folder="static",        # where js/ lives
)

# ↓ keep this import at the end to avoid circular imports
from . import routes               # noqa: E402,F401