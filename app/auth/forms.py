"""
app/auth/forms.py
-----------------
WTForms-powered HTML forms for the authentication blueprint.
"""

from flask_wtf          import FlaskForm
from wtforms            import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import (DataRequired, Email, EqualTo, Length,
                                 ValidationError)

from app.models import User         # the SQLAlchemy User model you’ll create


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #
def _email_exists(email: str) -> bool:
    """Return True if *email* is already registered (case-insensitive)."""
    return User.query.filter(User.email.ilike(email)).first() is not None


# --------------------------------------------------------------------------- #
# Forms                                                                       #
# --------------------------------------------------------------------------- #
class RegisterForm(FlaskForm):
    """Basic sign-up form (local account)."""

    email    = StringField("E-mail address",
                           validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Password",
                             validators=[DataRequired(),
                                         Length(min=8, message="≥ 8 characters please.")])
    confirm  = PasswordField("Confirm password",
                             validators=[DataRequired(),
                                         EqualTo("password", message="Passwords must match.")])
    submit   = SubmitField("Create account")

    # custom validator -------------------------------------------------------
    def validate_email(self, field):
        if _email_exists(field.data):
            raise ValidationError("That e-mail is already registered.")


class LoginForm(FlaskForm):
    """Local credentials sign-in (username/password)."""

    email      = StringField("E-mail",    validators=[DataRequired(), Email()])
    password   = PasswordField("Password", validators=[DataRequired()])
    remember   = BooleanField("Remember me")
    submit     = SubmitField("Log in")


class RequestResetForm(FlaskForm):
    """Ask for a password-reset email."""

    email  = StringField("E-mail", validators=[DataRequired(), Email()])
    submit = SubmitField("Send reset link")

    def validate_email(self, field):
        if not _email_exists(field.data):
            raise ValidationError("No account found for that e-mail address.")


class ResetForm(FlaskForm):
    password = PasswordField(
        "New password",
        validators=[DataRequired(), Length(min=8)]
    )
    confirm  = PasswordField(
        "Confirm new password",
        validators=[DataRequired(), EqualTo("password")]
    )
    submit   = SubmitField("Reset password")