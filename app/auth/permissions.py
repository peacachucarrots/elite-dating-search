# app/auth/permissions.py
from functools import wraps
from flask import abort
from flask_login import current_user

def require_role(name: str):
    """Abort with 403 unless current_user has the given role."""
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kw):
            if not current_user.is_authenticated or not current_user.has_role(name):
                abort(403)
            return fn(*args, **kw)
        return wrapper
    return deco

def require_level(min_level: int):
    """Abort 403 unless the logged-in user’s level ≥ min_level."""
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated or current_user.max_role_level() < min_level:
                abort(403)
            return fn(*args, **kwargs)
        return wrapper
    return deco