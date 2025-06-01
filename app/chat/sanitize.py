# app/chat/sanitize.py
import bleach

_ALLOWED_TAGS = ["br"]
_ALLOWED_ATTRS: dict[str, list[str]] = {}

def clean(text: str) -> str:
    return bleach.clean(text,
                        tags=_ALLOWED_TAGS,
                        attributes=_ALLOWED_ATTRS,
                        strip=True)