# app/program/routes.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import current_user, login_required
from flask_socketio import emit
from uuid import uuid4
from werkzeug.utils import secure_filename
from pathlib import Path

from app.data.testimonials import testimonials
from app.program.service import FIELD_LABELS
from .forms import CandidateForm, ClientForm
from ..models.program import ProgramApplication, ProgramType
from ..extensions import db

from . import bp

UPLOAD_DIR = Path("app/main/static/img/candidates")

@bp.route("/candidate", methods=["GET", "POST"])
@login_required
def candidate():
    form = CandidateForm()
    if form.validate_on_submit():
        photo_file = form.photo.data
        filename   = secure_filename(photo_file.filename)
        unique     = f"{uuid4().hex}_{filename}"
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        photo_file.save(UPLOAD_DIR / unique)

        data = form.data.copy()
        data.pop("csrf_token", None)
        data.update({
            "Program": "Candidate",
            "first_name": current_user.profile.first_name,
            "last_name": current_user.profile.last_name,
            "age": current_user.profile.age,
            "email": current_user.email,
            "phone": current_user.phone,
        })
        app = ProgramApplication(
            user_id   = current_user.id,
            program   = ProgramType.CANDIDATE,
            form_json = { **data, "photo": unique },
        )
        db.session.add(app)
        db.session.commit()

        flash("Application received – our matchmaking team will review shortly.",
              "success")
        return redirect(url_for("program.thank_you", kind="candidate"))

    return render_template("candidate.html",
                           form=form,
                           testimonials=testimonials)

@bp.route("/client", methods=["GET", "POST"])
@login_required
def client():
    form = ClientForm(obj=current_user)
    if form.validate_on_submit():
        photo_file = form.photo.data
        filename = secure_filename(photo_file.filename)
        unique = f"{uuid4().hex}_{filename}"
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        photo_file.save(UPLOAD_DIR / unique)

        data = form.data.copy()
        data.pop("csrf_token", None)
        data.update({
            "first_name": current_user.profile.first_name,
            "last_name": current_user.profile.last_name,
            "email": current_user.email,
            "phone": current_user.phone,
        })
        app = ProgramApplication(
            user_id    = current_user.id,
            program    = ProgramType.CLIENT,
            status     = "new",          # will become 'call_set' → 'ach_sent'…
            ach_signed = False,
            paid       = False,
            form_json  = data,
        )
        db.session.add(app)
        db.session.commit()

        flash("Application received – our matchmaking team will review shortly.",
              "success")
        return redirect(url_for("program.thank_you", kind="client"))

    return render_template("client.html", form=form)

@bp.route("/client/confirm", methods=["POST"])
@login_required
def client_confirm():
    session_id = request.args.get("session_id")
    if not session_id:
        return redirect(url_for("program.client"))

    return redirect(url_for("program.thank_you", kind="client"))

@bp.route("/thanks/<kind>")
@login_required
def thank_you(kind: str):
    if kind not in ("candidate", "client"):
        abort(404)

    if kind == "candidate":
        headline = "Application received — thank you!"
        blurb    = ("Our team will review your Candidate Program "
                    "application and contact you within 2 business days.")
    else:
        headline = "Application received — welcome aboard!"
        blurb    = ("Your dedicated matchmaker will reach out within 2 business days "
                    "to schedule your onboarding consultation.")

    return render_template(
        "thank_you.html",
        headline=headline,
        blurb=blurb,
        kind=kind
    )