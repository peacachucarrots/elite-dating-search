# app/program/forms.py
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileRequired, FileField
from wtforms import StringField, TelField, TextAreaField, SelectField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length
from werkzeug.utils   import secure_filename

class BaseProgramForm(FlaskForm):
    program   = HiddenField()

    # –– Contact –––––––––––––––––––
    street  = StringField("Street Address", validators=[Length(max=128)])
    city    = StringField("City",           validators=[Length(max=64)])
    state   = StringField("State",          validators=[Length(max=32)])
    zip     = StringField("ZIP / Postal",   validators=[Length(max=16)])
    country = SelectField("Country", choices=[("US","United States"), ("CA","Canada"), ("GB","United Kingdom"), ("other","Other")], validators=[DataRequired()])

    # –– About you ––––––––––––––––
    occupation = StringField("Occupation", validators=[DataRequired(), Length(max=64)])
    income_bracket = SelectField(
        "Annual Income",
        choices=[("0-100","< $100 K"), ("100-250","$100–250 K"), ("250-500","$250–500 K"), ("500+","$500 K+")],
        validators=[DataRequired()]
    )
    education = SelectField(
        "Education Level",
        choices=[("hs","High School"), ("ba","Bachelor"), ("ma","Master"), ("mba","MBA"), ("phd","PhD"), ("other","Other")],
        validators=[DataRequired()]
    )
    marital_status = SelectField(
        "Marital Status",
        choices=[("single","Single"), ("divorced","Divorced"), ("widowed","Widowed")],
    )

    ref_src = SelectField(
        "How did you hear about us?",
        choices=[("google","Google"), ("friend","Friend"), ("ig","Instagram"), ("podcast","Podcast"), ("other","Other")],
        validators=[DataRequired()]
    )

    intro = TextAreaField("Tell us a bit about yourself", validators=[Length(max=2000)])

    photo = FileField(
        "Upload a recent photo",
        validators=[
            FileAllowed(["jpg", "jpeg", "png", "webp"], "Images only!"),
            FileRequired("Please choose a photo.")
        ],
    )

    submit = SubmitField("Submit application")

class CandidateForm(BaseProgramForm):
    pass

class ClientForm(BaseProgramForm):
    pass