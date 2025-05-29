from flask import Blueprint

bp = Blueprint(
    "program",
    __name__,
    template_folder="templates",
    url_prefix="/program"
)

from . import routes       # noqa: E402  (placed last to avoid circulars)