# app/blog/__init__.py
from flask import Blueprint
bp = Blueprint("blog", __name__, template_folder="templates")
from . import routes           # noqa: E402  (register routes)