# app/main/routes.py
from flask import render_template, url_for, abort
from app.blog.data import POSTS     # single source of blog meta
from . import bp

# ──────────────────────────────────────────────────────────────────────────
# Home page – build “recent_posts” card list from POSTS
# ──────────────────────────────────────────────────────────────────────────
@bp.route("/")
def index():
    recent = [
        {
            "title": p["title"],
            "url":   url_for("blog.show_post", slug=p["slug"]),
            "img":   url_for("main.static", filename=p["thumb"]),   # ← change
        }
        for p in POSTS
    ]
    return render_template("index.html", recent_posts=recent)

# ──────────────────────────────────────────────────────────────────────────
# Static marketing pages
# ──────────────────────────────────────────────────────────────────────────
@bp.route("/matchmaking-services")
def matchmaking_services():
    return render_template("matchmaking_services.html")

@bp.route("/our-process")
def our_process():
    return render_template("our_process.html")

@bp.route("/roi-of-love")
def roi_of_love():
    return render_template("roi_of_love.html")

@bp.route("/testimonials")
def testimonials():
    # simple stub data; replace with real testimonials later
    sample = [
        {"name": "Dave & Rebecca",
         "quote": "I can honestly say ...",
         "image": url_for("static", filename="img/testimonials/dave_rebecca.jpg")},
    ]
    return render_template("testimonials.html", testimonials=sample)

@bp.route("/about-us")
def about_us():
    return render_template("about_us.html")

@bp.route("/get-started")
def get_started():
    return render_template("get_started.html")

@bp.route("/save-candidate")
def save_candidate():
    return render_template("save_candidate.html")

@bp.route("/candidate-program")
def candidate_program():
    return render_template("candidate_program.html")

@bp.route("/client-program")
def client_program():
    return render_template("client_program.html")