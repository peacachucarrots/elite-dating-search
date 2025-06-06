# app/main/routes.py
from flask import render_template, url_for, abort
from app.blog.data import POSTS
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
            "img":   url_for("main.static", filename=p["thumb"]),
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
    testimonials = [
        {
            "name": "Dave & Rebecca",
            "quote": ("I can honestly say that I have never been happier in my life. "
                "How can I put a price on finding someone I may spend the rest "
                "of my life with?"),
            "image": "dave-rebecca.jpg"
        },
        {
            "name": "Alex & Samantha",
            "quote": ("Elite Dating Search understood my hectic executive schedule "
                "and still found me someone who challenges and inspires me."),
            "image": "alex-samantha.jpg"
        },
        {
            "name": "Maria & Julio",
            "quote": ("Dating with intention changed everything. We were engaged "
                "nine months after our first date—thank you EDS!"),
            "image": "maria-julio.jpg"
        }
    ]
    return render_template("testimonials.html", testimonials=testimonials)

@bp.route("/about-us")
def about_us():
    return render_template("about_us.html")

@bp.route("/get-started")
def get_started():
    return render_template("get_started.html")