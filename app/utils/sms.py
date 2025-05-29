# app/utils/sms.py
from os import getenv
from twilio.rest import Client
from flask import current_app as app

_client = Client(getenv("TWILIO_SID"), getenv("TWILIO_AUTH"))

def send_sms(to: str, body: str) -> None:
    if app.debug:  # dev mode → don’t hit real SMS
        print(f"[DEV SMS → {to}] {body}")
        return