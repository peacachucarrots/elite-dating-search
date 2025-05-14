# app/models/__init__.py
from app.extensions import db

# import model modules so they register with SQLAlchemy metadata
from .user import User   # noqa: F401
# from .post import Post   # noqa: F401
# from .payment import Payment  # noqa: F401

__all__ = ["db", "User"]