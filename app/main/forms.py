# main/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, HiddenField
from wtforms.validators import DataRequired, Email, Length

class ContactForm(FlaskForm):
    name    = StringField("Name",   validators=[DataRequired(), Length(max=80)])
    email   = StringField("Email",  validators=[DataRequired(), Email(), Length(max=120)])
    subject = StringField("Subject")
    message = TextAreaField("Message", validators=[DataRequired(), Length(max=2000)])

    # Anti-spam hidden fields
    website = StringField()
    ts = HiddenField()