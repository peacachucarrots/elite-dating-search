"""
Authentication blueprint factory.

Keeps all auth-related routes, templates and (optionally) static files
under the “/auth/…” URL prefix.
"""

from flask import Blueprint

# ---------------------------------------------------------------------------
# Blueprint object
# ---------------------------------------------------------------------------
bp = Blueprint(
    "auth",                       # blueprint name
    __name__,                     # import name
    url_prefix="/auth",           # every route becomes /auth/…
    template_folder="templates",  # auth/templates/…
    static_folder="static"        # optional – auth/static/…
)

# ---------------------------------------------------------------------------
# Lazy-import the route modules so they can register view functions
# ---------------------------------------------------------------------------
from app.auth import routes, forms   # noqa: E402,F401