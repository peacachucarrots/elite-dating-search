# app/admin/__init__.py
from flask import Blueprint, abort
from flask_login import current_user
from functools import wraps
from ..models import Role

bp = Blueprint("admin", __name__, url_prefix="/admin")

def admin_required(view):
    """Abort 403 unless current user has the 'admin' role."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not (current_user.is_authenticated and
                any(r.name == "admin" for r in current_user.roles)):
            abort(403)
        return view(*args, **kwargs)
    return wrapped

from . import routes  # noqa