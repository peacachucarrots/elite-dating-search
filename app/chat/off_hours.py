# chat/off_hours.py
from datetime import datetime, timedelta
from sqlalchemy.orm import aliased
from sqlalchemy.sql import func, desc
from app.models import ChatSession, Message, User, Profile
from app.extensions import db
from .utils import is_off_hours        # to know “when” later
from app.settings import EASTERN, OFFICE_OPEN, OFFICE_CLOSE

def last_completed_window(now: datetime | None = None) -> tuple[datetime, datetime]:
    """
    Return (start, end) for the most recent *finished* off-hours window:
        • Between 18:00 and 09:00 Eastern
        • Always ends at today’s 09:00 ET
    """
    now = now or datetime.now(tz=EASTERN)

    today_open  = datetime.combine(now.date(), OFFICE_OPEN,  tzinfo=EASTERN)
    today_close = datetime.combine(now.date(), OFFICE_CLOSE, tzinfo=EASTERN)

    if now < today_open:          # 00:00-08:59  → we’re still before opening
        end   = today_open
        start = today_close - timedelta(days=1)   # yesterday 18:00
    else:                         # 09:00-23:59 (incl. after hours)
        end   = today_open        # today 09:00
        start = today_close - timedelta(days=1)   # yesterday 18:00

    return start, end

def overnight_chats():
    """
    Return [(chat_id, username, preview)], newest first, for chats that have at
    least one *visitor* message since 18:00 of the previous business day and
    before 09:00 this morning.
    """
    start, end = last_completed_window()

    # Step-2: sub-query for latest visitor msg per chat in that window
    Msg1 = aliased(Message)
    subq = (
        db.session.query(
            Msg1.chat_id.label("cid"),
            func.max(Msg1.ts).label("last_ts"),
        )
        .filter(Msg1.author == "visitor",
                Msg1.ts.between(start, end))
        .group_by(Msg1.chat_id)
        .subquery()
    )

    # Step-3: fetch full row (chat_id, body, ts, username)
    Msg2 = aliased(Message)
    UserAlias = aliased(User)
    ProfAlias = aliased(Profile)

    rows = (
        db.session.query(
            ChatSession.id,

            func.coalesce(
                func.concat_ws(' ', ProfAlias.first_name, ProfAlias.last_name),
                UserAlias.email,  # or .username if you add it later
                "Visitor"
            ).label("display_name"),

            UserAlias.email.label("email"),
            Msg2.body,
            Msg2.ts,
        )
        .join(subq, ChatSession.id == subq.c.cid)
        .join(Msg2,
              (Msg2.chat_id == ChatSession.id) &
              (Msg2.ts == subq.c.last_ts))
        .join(UserAlias, ChatSession.user_id == UserAlias.id)
        .outerjoin(ProfAlias, ProfAlias.user_id == UserAlias.id)
        .order_by(desc(Msg2.ts))
        .all()
    )

    return [(cid, uname, email, body) for cid, uname, email, body, _ in rows]