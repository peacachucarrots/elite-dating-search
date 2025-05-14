# app/main/__init__.py
"""Main (marketing) blueprint: landing page, static content pages."""

from flask import Blueprint

# Blueprint arguments:
#   name:         'main'  → used in url_for("main.index")
#   import_name:  __name__ (module path)
#   template_folder / static_folder are relative to this file
bp = Blueprint(
    "main",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/main/static"
)

# Import routes so the view functions are associated with `bp`.
# Keep this at the *bottom* to avoid circular-import issues.
from . import routes  # noqa: E402,F401