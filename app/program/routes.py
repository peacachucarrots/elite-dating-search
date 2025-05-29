# app/program/routes.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import current_user, login_required
from stripe import PaymentIntent, error as stripe_error

from .forms import CandidateForm, ClientForm
from ..models.program import ProgramApplication
from ..extensions import db, stripe

from . import bp

@bp.route("/candidate", methods=["GET", "POST"])
@login_required
def candidate():
    form = CandidateForm(program="candidate")
    if form.validate_on_submit():
        app = ProgramApplication(
            user_id=current_user.id,
            program="candidate",

            street=form.street.data,
            city=form.city.data,
            state=form.state.data,
            zip=form.zip.data,
            country=form.country.data,

            occupation=form.occupation.data,
            income_bracket=form.income_bracket.data,
            education=form.education.data,
            marital_status=form.marital_status.data,

            ref_src=form.ref_src.data,
            intro=form.intro.data
        )
        db.session.add(app); db.session.commit()
        flash("Application received – our matchmaking team will review shortly.", "success")
        return redirect(url_for("program.thank_you", kind="candidate"))

    return render_template("candidate.html", form=form)

@bp.route("/client", methods=["GET", "POST"])
@login_required
def client():
    form = ClientForm(obj=current_user)
    if form.validate_on_submit():
        app = ProgramApplication(
            user_id=current_user.id,
            program="client",

            street=form.street.data,
            city=form.city.data,
            state=form.state.data,
            zip=form.zip.data,
            country=form.country.data,

            occupation=form.occupation.data,
            income_bracket=form.income_bracket.data,
            education=form.education.data,
            marital_status=form.marital_status.data,

            ref_src=form.ref_src.data,
            intro=form.intro.data
        )
        db.session.add(app); db.session.commit()

        # create Stripe PaymentIntent (e.g. $7 500 USD)
        checkout_session = stripe.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "unit_amount": 7_500_00,  # cents
                    "product_data": {"name": "Elite Dating Client Program fee"},
                },
                "quantity": 1,
            }],
            success_url=url_for("program.thank_you", kind="client", _external=True),
            cancel_url=url_for("program.client", _external=True),
            metadata={"app_id": app.id},
        )
        return render_template(
            "client_checkout.html",
            stripe_pk=current_app.config["STRIPE_PUBLISHABLE_KEY"],
            stripe_session_id=checkout_session.id,
        )
    return render_template("client.html", form=form)

@bp.route("/client/confirm", methods=["POST"])
@login_required
def client_confirm():
    session_id = request.args.get("session_id")
    if not session_id:
        return redirect(url_for("program.client"))

    # 1) verify with Stripe (optional but recommended)
    checkout = stripe.checkout.Session.retrieve(session_id)
    if checkout.payment_status != "paid":
        return redirect(url_for("program.client"))

    # 2) mark the application paid
    app_id = checkout.metadata.get("app_id")
    app = ProgramApplication.query.get(app_id)
    if app and not app.fee_paid:
        app.fee_paid = True
        app.stripe_pi = checkout.payment_intent
        db.session.commit()

    # 3) off to the shared thank-you page
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
        headline = "Payment received — welcome aboard!"
        blurb    = ("Your dedicated matchmaker will reach out within 2 business days "
                    "to schedule your onboarding consultation.")

    return render_template(
        "thank_you.html",
        headline=headline,
        blurb=blurb,
        kind=kind
    )