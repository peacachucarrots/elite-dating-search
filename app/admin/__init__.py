# app/admin/__init__.py
from flask import Blueprint, abort
from flask_login import current_user
from functools import wraps
from ..models import Role

bp = Blueprint("admin", __name__, url_prefix="/admin")

from . import routes  # noqa