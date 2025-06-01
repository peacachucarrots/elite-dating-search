# app/program/routes.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import current_user, login_required
from flask_socketio import emit

from .forms import CandidateForm, ClientForm
from ..models.program import ProgramApplication
from ..extensions import db

from . import bp

@bp.route("/candidate", methods=["GET", "POST"])
@login_required
def candidate():
    form = CandidateForm()                     # no need program="…" in WTForm
    if form.validate_on_submit():

        app = ProgramApplication(
            user_id    = current_user.id,
            program    = ProgramType.CANDIDATE,
            status     = "new",
            form_json  = form.data,
        )
        db.session.add(app)
        db.session.commit()

        emit("new_program_app",
             {"app": to_dict(new_app)},
             room="reps", namespace="/")

        flash("Application received – our matchmaking team will review shortly.",
              "success")
        return redirect(url_for("program.thank_you", kind="candidate"))

    return render_template("candidate.html", form=form)

@bp.route("/client", methods=["GET", "POST"])
@login_required
def client():
    form = ClientForm(obj=current_user)
    if form.validate_on_submit():

        app = ProgramApplication(
            user_id    = current_user.id,
            program    = ProgramType.CLIENT,
            status     = "new",          # will become 'call_set' → 'ach_sent'…
            ach_signed = False,
            paid       = False,
            form_json  = form.data,
        )
        db.session.add(app)
        db.session.commit()

        emit("new_program_app",
             {"app": to_dict(new_app)},
             room="reps", namespace="/")

        flash("Application received – our matchmaking team will review shortly.",
              "success")
        # ⬇️  fixed   kind="client"
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