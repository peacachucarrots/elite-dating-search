"""
app/auth/forms.py
-----------------
WTForms-powered HTML forms for the authentication blueprint.
"""

from flask_wtf          import FlaskForm
from wtforms            import StringField, PasswordField, DateField, BooleanField, SelectField, SubmitField
from wtforms.validators import (DataRequired, Email, EqualTo, Length,
                                 ValidationError)

from app.models import User


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
                                         Length(min=8, message="Password must be at least 8 characters.")])
    confirm  = PasswordField("Confirm password",
                             validators=[DataRequired(),
                                         EqualTo("password", message="Passwords must match.")])
    first_name = StringField("First name", validators=[DataRequired()])
    last_name = StringField("Last name", validators=[DataRequired()])
    phone = StringField("Phone Number",
                        validators=[DataRequired(), Length(min=8, max=20)])
    dob = DateField("Date of birth (MM-DD-YYYY)",
                    validators=[DataRequired()], format="%m-%d-%Y")
    gender = SelectField(
        "Gender",
        choices=[("male", "Male"), ("female", "Female"),
                 ("nonbinary", "Non-binary"), ("other", "Other")],
        validators=[DataRequired()]
    )
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

class OtpForm(FlaskForm):
    code = StringField("6-digit code", validators=[DataRequired(), Length(6, 6)])
    submit = SubmitField("Verify")


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