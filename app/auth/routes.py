# app/auth/routes.py
from datetime import datetime

from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, request, current_app
)
from flask_login import login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from app import db
from app.models.user import User
from .forms import RegisterForm, LoginForm, RequestResetForm, ResetForm
from .email import send_confirmation_email, send_password_reset
from . import bp

# --------------------------------------------------------------------------- #
# helpers                                                                     #
# --------------------------------------------------------------------------- #
def get_ts() -> URLSafeTimedSerializer:
    """Return a per-request serializer bound to the current app’s secret key."""
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


# --------------------------------------------------------------------------- #
# Register & confirm e-mail                                                   #
# --------------------------------------------------------------------------- #
@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            email=form.email.data.lower().strip(),
            pw_hash=User.hash_password(form.password.data),
        )
        db.session.add(user)
        db.session.commit()

        # ── e-mail verification ───────────────────────────────
        send_confirmation_email(user)  # generates its own token
        flash("Check your inbox to confirm your e-mail.", "info")

        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@bp.route("/confirm/<token>")
def confirm_email(token):
    try:
        email = get_ts().loads(token, salt="email-confirm", max_age=86_400)  # 24 h
    except (SignatureExpired, BadSignature):
        flash("Confirmation link is invalid or has expired.", "danger")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=email).first_or_404()
    if not user.is_verified:
        user.is_verified = True
        db.session.commit()
        flash("E-mail verified — you can now log in.", "success")
    else:
        flash("E-mail was already verified.", "info")

    return redirect(url_for("auth.login"))


# --------------------------------------------------------------------------- #
# Login / logout                                                              #
# --------------------------------------------------------------------------- #
@bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if not user or not user.check_password(form.password.data):
            flash("Invalid credentials.", "danger")
            return redirect(url_for("auth.login"))

        login_user(user, remember=form.remember.data)
        user.last_login = datetime.utcnow()
        db.session.commit()
        return redirect(request.args.get("next") or url_for("main.index"))

    return render_template("auth/login.html", form=form)


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.", "info")
    return redirect(url_for("main.index"))


# --------------------------------------------------------------------------- #
# Password-reset: request link                                                #
# --------------------------------------------------------------------------- #
@bp.route("/reset", methods=["GET", "POST"])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and user.is_verified:            # send only to verified users
            token = get_ts().dumps(user.email, salt="pw-reset")
            send_reset_email(user)               # ✔ helper will embed the token
        # Always show the same message — don’t leak which e-mails exist
        flash(
            "If that e-mail is registered, a reset link is on its way.",
            "info"
        )
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_request.html", form=form)


# --------------------------------------------------------------------------- #
# Password-reset: form reached via token                                      #
# --------------------------------------------------------------------------- #
@bp.route("/reset/<token>", methods=["GET", "POST"])
def reset_password(token):
    try:
        email = get_ts().loads(token, salt="pw-reset", max_age=3_600)  # 1 h
    except (SignatureExpired, BadSignature):
        flash("Your reset link is invalid or has expired.", "danger")
        return redirect(url_for("auth.reset_request"))

    user = User.query.filter_by(email=email).first_or_404()
    form = ResetForm()
    if form.validate_on_submit():
        user.pw_hash = User.hash_password(form.password.data)
        db.session.commit()
        flash("Password updated — please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", form=form)