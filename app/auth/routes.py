# app/auth/routes.py
from datetime import datetime, timedelta
from secrets import randbelow

from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, request, current_app, session
)
from flask_login import login_user, logout_user, login_required, current_user

from app import db
from app.models.user import User
from app.models.role import Role
from app.models.profile import Profile
from app.utils.email_tokens import generate_token, verify_token
from app.utils.sms import send_sms
from .forms import RegisterForm, LoginForm, RequestResetForm, ResetForm, OtpForm
from .email import send_confirmation_email, send_password_reset
from . import bp

OTP_LIFETIME = timedelta(minutes=5)

# --------------------------------------------------------------------------- #
# Register & confirm e-mail                                                   #
# --------------------------------------------------------------------------- #
@bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            email=form.email.data.lower().strip(),
            pw_hash=User.hash_password(form.password.data),
            phone=form.phone.data
        )

        user.roles.append(Role.query.filter_by(name="visitor").one())

        # profile
        prof = Profile(
            first_name=form.first_name.data.strip(),
            last_name=form.last_name.data.strip(),
            dob=form.dob.data,
            gender=form.gender.data
        )
        user.profile = prof

        db.session.add(user)
        db.session.commit()

        # ── e-mail verification ───────────────────────────────
        send_confirmation_email(user)
        flash("Check your inbox to confirm your e-mail.", "info")

        return redirect(url_for("main.index"))

    return render_template("auth/register.html", form=form)


@bp.route("/confirm/<token>")
def confirm_email(token):
    uid = verify_token(token, purpose="email-confirm", max_age=86_400)
    if not uid:
        flash("Confirmation link is invalid or has expired.", "danger")
        return redirect(url_for("auth.login"))

    user = User.query.get_or_404(uid)
    if not user.is_verified:
        user.is_verified = True
        db.session.commit()
        flash("E-mail verified — you can now log in.", "success")
    else:
        flash("E-mail was already verified.", "info")

    return redirect(url_for("auth.login"))

@bp.route("/resend-email", endpoint="resend_email_token", methods=["GET"])
def resend_email_token():
    """
    Re-send the “confirm your e-mail” message for an un-verified account.

    We expect ?email=<adress> in the query-string (login() adds it).
    """
    email = request.args.get("email", "").strip().lower()
    user  = User.query.filter_by(email=email).first_or_404()

    if user.is_verified:
        flash("That address is already confirmed – just log in ✨", "info")
        return redirect(url_for("auth.login"))

    # create and send a fresh confirmation link
    token       = generate_token(user.id, purpose="verify")
    confirm_url = url_for("auth.confirm_email", token=token, _external=True)
    send_confirmation_email(user, confirm_url)

    flash("We’ve sent a new confirmation link – check your inbox.", "success")
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
            return render_template("auth/login.html", form=form)

        if not user.is_verified:
            flash("Confirm your e-mail first.", "warning")
            return redirect(url_for("auth.resend_email_token", email=user.email))

        code = f"{randbelow(1_000_000):06d}"  # zero-padded 6-digits
        user.phone_otp = code
        user.phone_otp_sent = datetime.utcnow()
        db.session.commit()

        send_sms(user.phone, f"Your EliteDatingSearch code is: {code}")

        session["pending_uid"] = user.id
        return redirect(url_for("auth.verify_phone"))

    return render_template("auth/login.html", form=form)

@bp.route("/verify-phone", methods=["GET", "POST"])
def verify_phone():
    if "pending_uid" not in session:
        return redirect(url_for("auth.login"))

    user = User.query.get(session["pending_uid"])
    form = OtpForm()
    if form.validate_on_submit():
        if (user.phone_otp == form.code.data
                and datetime.utcnow() - user.phone_otp_sent < OTP_LIFETIME):
            user.phone_otp = None
            user.phone_otp_sent = None
            user.is_phone_verified = True
            db.session.commit()

            login_user(user)
            session.pop("pending_uid", None)
            flash("Logged in successfully", "success")
            return redirect(url_for("main.index"))

        flash("Invalid or expired code.", "danger")

    return render_template("auth/phone_otp.html", form=form, phone=user.phone)


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
        if user and user.is_verified:
            send_password_reset(user)
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
    uid = verify_token(token, purpose="pw-reset", max_age=3_600)
    if not uid:
        flash("Your reset link is invalid or has expired.", "danger")
        return redirect(url_for("auth.reset_request"))

    user = User.query.get_or_404(uid)
    form = ResetForm()
    if form.validate_on_submit():
        user.pw_hash = User.hash_password(form.password.data)
        db.session.commit()
        flash("Password updated — please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", form=form)