# app/blog/routes.py
from flask import render_template, abort
from . import bp
from .data import POSTS

def _find(slug):
    return next((p for p in POSTS if p["slug"] == slug), None)

@bp.route("/blog/<slug>")
def show_post(slug):
    post = _find(slug)
    if not post:
        abort(404)
    return render_template(f"blog/{slug}.html", post=post)