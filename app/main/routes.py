# app/main/routes.py
from flask import render_template, url_for, flash, redirect, current_app, request
from app.blog.data import POSTS
from app.data.testimonials import TESTIMONIALS
from app.main.forms import ContactForm
from app.utils.email_tokens import send_support_email
from app.extensions import limiter
import time
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
#
@bp.route("/testimonials")
def testimonials():
    return render_template("testimonials.html", testimonials=TESTIMONIALS)

@bp.route("/about-us")
def about_us():
    return render_template("about_us.html")

@bp.route("/get-started")
def get_started():
    return render_template("get_started.html")

@bp.route("/privacy")
def privacy():
    return render_template("legal/privacy.html")

@bp.route("/terms")
def terms():
    return render_template("legal/terms.html")

@bp.route("/contact", methods=["GET", "POST"])
@limiter.limit('2/minute;10/day')
def contact():
    form = ContactForm()
    if request.method == "GET":
        form.ts.data = int(time.time())
    if form.validate_on_submit():
        if form.website.data:
            current_app.logger.info("Honeypot hit – dropped.")
            return '', 204
        if time.time() - int(form.ts.data) < 3:
            flash('Too quick — please try again.')
            return redirect(url_for('main.contact'))
        send_support_email(form.name.data, form.email.data, form.subject.data, form.message.data)
        flash('Thanks! Your message was sent.')
        return redirect(url_for('main.contact'))
    return render_template('contact.html', form=form, ts=int(time.time()))