# app/chat/routes.py
"""
Live-chat blueprint: HTTP view for /rep plus all Socket.IO event handlers.
All in-memory state lives here (ALIVE, VISITORS, etc.). Swap for a DB later.
"""

from collections import defaultdict
from datetime import datetime

from flask import Blueprint, render_template, request, abort, current_app, flash, redirect, url_for
from flask_socketio import emit, join_room, leave_room
from flask_login import current_user, logout_user, login_required

from sqlalchemy import func, desc

from app.auth.permissions import require_role, require_level
from app.chat.faq import FAQ
from app.chat.off_hours import overnight_chats
from app.chat.sanitize import clean
from app.chat.utils import reps_are_online, is_off_hours
from app.extensions import socketio, db
from app.models.chat import ChatSession, Message
from app.models.program import ProgramApplication, ProgramType
from app.models.role import Role
from app.models.user import User
from app.program.service import latest_program_apps, FIELD_LABELS
from . import bp

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def _create_session_for(user_id, socket_sid) -> ChatSession:
    """Create the *next* numbered session for this user."""
    if user_id is None:
        return ChatSession(user_id=None, socket_sid=socket_sid, seq=-1)

    next_seq = (
        db.session.query(func.coalesce(func.max(ChatSession.seq), 0))
        .filter_by(user_id=user_id)
        .scalar()
    ) + 1

    chat = ChatSession(user_id=user_id, socket_sid=socket_sid, seq=next_seq)
    db.session.add(chat)
    db.session.commit()
    return chat

def current_session_for_socket(sid: str) -> ChatSession | None:
    """Look up the DB row that belongs to this socket."""
    chat_id = SID_TO_SESSION.get(sid)
    return ChatSession.query.get(chat_id) if chat_id else None

def _display_name(user: User) -> str:
    """
    First-name + last-name if both exist,
    otherwise the part before “@” in the e-mail.
    """
    if user.profile and user.profile.first_name and user.profile.last_name:
        return f"{user.profile.first_name} {user.profile.last_name}"
    return user.email.split("@")[0]

# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------
@bp.route("/rep")
@login_required
@require_level(20)
def rep_dashboard():
    return render_template("rep.html")

@bp.route("/candidates")
@login_required
@require_level(20)
def candidate_list():
    apps = (
        ProgramApplication.query
        .filter_by(program=ProgramType.CANDIDATE)
        .order_by(ProgramApplication.status.desc(),
                  ProgramApplication.submitted.desc())
        .all()
    )
    return render_template("rep/candidate_list.html", apps=apps)

@bp.route("/candidate/<int:app_id>")
@login_required
@require_level(20)
def candidate_detail(app_id):
    app = ProgramApplication.query.get_or_404(app_id)
    data = {
        FIELD_LABELS.get(k, k.replace('_', ' ').title()): v
        for k, v in app.form_json.items()
    }
    return render_template("rep/candidate_detail.html", app=app, answers=data, FIELD_LABELS=FIELD_LABELS)

@bp.route("/clients")
@login_required
@require_level(20)
def client_list():
    apps = (
        ProgramApplication.query
        .filter_by(program=ProgramType.CLIENT)
        .order_by(ProgramApplication.submitted.desc())
        .all()
    )
    return render_template("rep/client_list.html", apps=apps)

@bp.route("/client/<int:app_id>")
@login_required
@require_level(20)
def client_detail(app_id):
    app = ProgramApplication.query.get_or_404(app_id)
    data = {
        FIELD_LABELS.get(k, k.replace('_', ' ').title()): v
        for k, v in app.form_json.items()
    }
    return render_template("rep/client_detail.html", app=app, answers=data, FIELD_LABELS=FIELD_LABELS)

@bp.route("/client/<int:app_id>/status", methods=["POST"])
@login_required
@require_level(20)
def update_client_status(app_id: int):
    """Rep marks a paid-client application as Paid / In-Progress / Done …"""
    if not current_user.has_role("rep"):
        abort(403)

    app = ProgramApplication.query.get_or_404(app_id)
    app.status = request.form.get("status", app.status)
    app.paid   = bool(request.form.get("paid"))
    app.ach_signed = bool(request.form.get("ach_signed"))

    db.session.commit()
    flash("Application status updated.", "success")

    return redirect(url_for("chat.client_detail", app_id=app_id))

# ---------------------------------------------------------------------------
# In-memory state (replace with DB when needed)
# ---------------------------------------------------------------------------
ALIVE: set[str]          = set()          # sockets currently connected
VISITORS: set[str]       = set()          # idle visitors
NEW_CHATS: set[str]      = set()          # visitors who sent 1st msg
REPS: set[str]           = set()          # active representatives
PAIR: dict[str, str]     = {}             # rep_sid ➜ visitor_sid
SID_TO_USER              = {}             # visitor_sid ➜ user.id
SID_TO_NAME              = {}             # visitor_sid ➜ display_name
SID_TO_SESSION           = {}             # visitor_sid ➜ chat.id
WAITING_DESC: set[str]   = set()          # chose 'human' but no response yet

def create_guest_user(name):
    u = User(email=None, pw_hash=None, is_active=False)
    u.roles.append(Role.query.filter_by(name="visitor").first())
    db.session.add(u); db.session.commit()
    return u

# ---------------------------------------------------------------------------
# Socket.IO lifecycle
# ---------------------------------------------------------------------------
@socketio.on("connect")
def handle_connect(auth):
    if current_user.is_authenticated:
        user       = current_user
        user_id    = user.id
        role       = (
            "admin"   if user.has_role("admin")  else
            "rep"     if user.has_role("rep")    else
            "client"  if user.has_role("client") else
            "visitor"
        )
        display_name = _display_name(user)
    else:
        user_id      = None
        role         = "visitor"
        display_name = (auth or {}).get("display_name") or "Visitor"

    sid = request.sid
    now_dt  = datetime.utcnow()
    now_iso = now_dt.isoformat(timespec="seconds")

    ALIVE.add(sid)
    SID_TO_NAME[sid] = display_name
    SID_TO_USER[sid] = user_id

    match role:
        case "visitor" | "client":
            if user_id is not None:
                chat = (
                    ChatSession.query
                    .filter_by(user_id=user_id, closed_at=None)
                    .order_by(ChatSession.opened_at.desc())
                    .first()
                )
            else:
                chat = None

            created_new = chat is None
            if created_new:
                chat = _create_session_for(user_id, sid)

                greeting = "Hi! What can I help you with today?"
                emit(
                    "visitor_msg",
                    {"body": greeting, "author": "assistant", "ts": now_iso},
                    room=sid,
                )
                if user_id is not None:
                    db.session.add(
                        Message(
                            chat_id=chat.id,
                            author="assistant",
                            body=greeting,
                            ts=now_dt,
                            user_id=user_id,
                        )
                    )
                    db.session.commit()

            SID_TO_SESSION[sid] = chat.id
            VISITORS.add(sid)

            if created_new and not reps_are_online():
                off_msg = (
                    "Our representatives are available 9 a.m.–6 p.m. ET, "
                    "Monday-Friday. Feel free to leave a message and we’ll "
                    "reach out via email typically within the next business day."
                )
                emit(
                    "rep_msg",
                    {"body": off_msg, "author": "assistant", "ts": now_iso},
                    room=sid,
                )
                db.session.add(
                    Message(
                        chat_id=chat.id,
                        author="assistant",
                        body=off_msg,
                        ts=now_dt,
                        user_id=user_id,
                    )
                )

            options = [{"id": k, "label": v["label"]} for k, v in FAQ.items()]
            if reps_are_online():
                options.append({"id": "human", "label": "Connect me to a representative"})
            emit("quick_options", {"options": options}, room=request.sid)

            if not created_new:
                for m in (
                    Message.query
                    .filter_by(chat_id=chat.id)
                    .order_by(Message.ts)
                    .all()
                ):
                    emit(
                        "visitor_msg",
                        {"body": m.body, "author": m.author, "ts": m.ts.isoformat()},
                        room=sid,
                    )

            emit("visitor_online", {"sid": sid, "username": display_name}, room="reps")
            current_app.logger.debug("+++ Visitor/Client connected %s", display_name)
            db.session.commit()
            return
        case "rep":
            if not current_user.has_role("rep"):
                emit("system", {"body": "You are not authorized as a representative."}, room=sid)
                return

            REPS.add(sid)
            join_room("reps")
            emit(
                "visitor_msg",
                {
                    "body": "Looking to chat? Tap the Rep Dashboard in the top right "
                            "for a more comprehensive view.",
                    "author": "assistant",
                    "ts": now_iso,
                },
                room=sid,
            )
            current_app.logger.debug("+++ Rep connected %s", display_name)
            return
        case "admin":
            if not current_user.is_authenticated:
                emit("system", "You need to sign in as an admin first.")
                return
            if not current_user.has_role("admin"):
                emit("system", "You are not authorized as an admin.")
                return
            emit("visitor_msg",
                 {"body": f"Welcome Admin {current_user.profile.first_name}!",
                  "author": "assistant",
                  "ts": now_iso},
                 room=request.sid)
            current_app.logger.debug("+++ Admin connected", display_name)
            return
        case _:
            current_app.logger.debug(f"!!! Unknown role '{role}' for SID {request.sid}. Treating as a visitor...")
            VISITORS.add(request.sid)
            join_room(request.sid)
            emit("visitor_online", {"sid": request.sid}, room="reps")
            current_app.logger.debug("+++ Unknown Role connected", request.sid)

@socketio.on("disconnect")
def handle_disconnect(auth):
    sid = request.sid
    timestamp = datetime.utcnow().isoformat(timespec="seconds")

    # ── Fast look-ups ──────────────────────────────────────────────
    is_rep      = sid in REPS
    visitor_sid = PAIR.pop(sid, None) if is_rep else sid
    username    = SID_TO_NAME.get(sid)

    # ── Global clean-up ────────────────────────────────────────────
    ALIVE.discard(sid)
    REPS.discard(sid)
    VISITORS.discard(sid)
    NEW_CHATS.discard(sid)

    SID_TO_SESSION.pop(sid, None)
    SID_TO_USER.pop(sid, None)
    SID_TO_NAME.pop(sid, None)

    # ── If a REP closed ───────────────────────────────────────────
    if is_rep and visitor_sid:
        emit("system",
             {"body": "Representative disconnected.",
              "author": "system",
              "ts": timestamp},
             room=visitor_sid)

        # return visitor to lobby if still online
        if visitor_sid in ALIVE:
            VISITORS.add(visitor_sid)
            emit("visitor_online",
                 {"sid": visitor_sid,
                  "username": SID_TO_NAME.get(visitor_sid)},
                 room="reps")

    # ── If a VISITOR closed ───────────────────────────────────────
    elif not is_rep:
        rep_sid = next((r for r, v in PAIR.items() if v == sid), None)
        if rep_sid:
            emit("system",
                 {"body": "Visitor disconnected.",
                  "author": "system",
                  "ts": datetime.utcnow().isoformat(timespec="seconds")},
                 room=rep_sid)
            PAIR.pop(rep_sid, None)

        emit("visitor_offline", {"sid": sid}, room="reps")

    chat_id = SID_TO_SESSION.get(visitor_sid)
    if chat_id:
        still_live = any(
            sid != visitor_sid and
            SID_TO_SESSION.get(sid) == chat_id and
            sid in ALIVE
            for sid in SID_TO_SESSION.keys()
        )
        if not still_live:
            chat = ChatSession.query.get(chat_id)
            if chat and chat.closed_at is None:
                chat.closed_at = datetime.utcnow()
                db.session.commit()

# ---------------------------------------------------------------------------
# Rep dashboard actions
# ---------------------------------------------------------------------------
@socketio.on("iam_rep")
@require_level(20)
def mark_rep():
    # Remove this socket from visitor pool
    REPS.add(request.sid)
    if request.sid in VISITORS:
        VISITORS.discard(request.sid)
        emit("visitor_offline", {"sid": request.sid}, room="reps")

    join_room("reps")

    for v in VISITORS:
        emit("visitor_online",
             {"sid": v, "username": SID_TO_NAME.get(v)},
             room=request.sid)

    for v in NEW_CHATS:
        emit("new_chat",
             {"sid": v, "username": SID_TO_NAME.get(v)},
             room=request.sid)

    for chat_id, username, email, preview in overnight_chats():
        emit("after_hours_chat",
             {"chat_id": chat_id,
              "username": username,
              "email": email,
              "preview": preview},
             room=request.sid)

    socketio.emit("program_apps",
                  {"apps": latest_program_apps()},
                  room=request.sid)

@socketio.on("mark_replied")
@require_level(20)
def mark_replied(data):
    """Rep clicked the 'Replied via e-mail' button."""
    chat_id = data["chat_id"]
    sess = ChatSession.query.get(chat_id)
    if not sess:
        emit("system",
             {"body": "Chat not found.",
              "author": "system",
              "ts": datetime.utcnow().isoformat(timespec="seconds")},
             room=request.sid)
        return

    sess.replied_via_email = True
    sess.closed_at = sess.closed_at or datetime.utcnow()
    db.session.commit()

    # tell just this rep to hide the chat row
    emit("prev_chat_remove", {"chat_id": chat_id}, room=request.sid)

@socketio.on("join_visitor")
@require_level(20)
def join_visitor(data):
    """
    Rep dashboard requests to handle a visitor *or* an after-hours chat.
    Payload:
        { sid: "<visitor SID>" }      – live visitor currently online
      or
        { chat_id: "<chat id>" }      – offline session from “After-hours”
    """
    rep_sid = request.sid

    # ── 0 · Identify the chat & user context ────────────────────────────
    visitor_sid = data.get("sid")
    if visitor_sid:                                   # live branch
        chat_id   = SID_TO_SESSION.get(visitor_sid)
        user_id   = SID_TO_USER.get(visitor_sid)
        live      = True
    else:                                             # after-hours branch
        chat_id   = data["chat_id"]
        session   = ChatSession.query.get(chat_id)
        if not session:
            emit("system",
                 {"body": "Chat not found.",
                  "author": "system",
                  "ts": datetime.utcnow().isoformat(timespec="seconds")},
                 room=rep_sid)
            return
        user_id   = session.user_id
        visitor_sid = None
        live      = False

    # ── 1 · Previous (closed) sessions list  ────────────────────────────
    prev_sessions = (ChatSession.query
                     .filter(ChatSession.user_id == user_id,
                             ChatSession.id != chat_id,
                             ChatSession.closed_at.isnot(None))
                     .order_by(desc(ChatSession.opened_at))
                     .all())

    emit("session_list", [
        {"chat_id": s.id,
         "label":   f"{s.seq:04d}",
         "opened":  s.opened_at.isoformat(timespec="seconds"),
         "closed":  s.closed_at.isoformat(timespec="seconds")}
        for s in prev_sessions
    ], room=rep_sid)

    # ── 2 · Replay entire transcript  ───────────────────────────────────
    history = (Message.query
               .filter_by(chat_id=chat_id)
               .order_by(Message.ts)
               .all())

    for m in history:
        emit("visitor_msg",
             {"body":   m.body,
              "author": m.author,
              "ts":     m.ts.isoformat(timespec="seconds")},
             room=rep_sid)

    # ── 3 · Live-visitor housekeeping  ─────────────────────────────────
    if live and visitor_sid:
        # pair sockets
        PAIR[rep_sid] = visitor_sid
        join_room(visitor_sid)

        # notify visitor (but not the rep who’s sending)
        emit("system",
             {"body": f"Representative {current_user.profile.first_name} has joined the chat.",
              "author": "system",
              "ts": datetime.utcnow().isoformat(timespec="seconds")},
             room=visitor_sid, include_self=False)

        # notify rep
        emit("system",
             {"body": f"You joined {SID_TO_NAME.get(visitor_sid, visitor_sid[:8])}",
              "author": "system",
              "ts": datetime.utcnow().isoformat(timespec="seconds")},
             room=rep_sid)

        # move visitor from VISITORS → paired
        VISITORS.discard(visitor_sid)
        NEW_CHATS.discard(visitor_sid)
        emit("new_chat_remove", {"sid": visitor_sid}, room="reps")

    # ── 4 · Ready flag for front-end UI  ────────────────────────────────
    emit("live_chat_ready", room=rep_sid)

    # ── 5 · log for debugging  ─────────────────────────────────────────-
    current_app.logger.debug(f"### rep {rep_sid[:8]} joined chat {chat_id} "
          f"({'live' if live else 'after-hours'})")

@socketio.on("leave_visitor")
@require_level(20)
def leave_visitor(data):
    """Rep clicks “End chat”. Unpair and put visitor back in the lobby."""
    visitor_sid = data.get("sid")
    rep_sid     = request.sid

    # ── Validate ───────────────────────────────────────────────────────────────
    if PAIR.get(rep_sid) != visitor_sid:
        emit("system",
             {"body": "No visitor selected.",
              "author": "system",
              "ts": datetime.utcnow().isoformat(timespec="seconds")},
             room=rep_sid)
        return

    # ── Break the pairing & leave the visitor room ─────────────────────────────
    PAIR.pop(rep_sid, None)
    leave_room(visitor_sid)

    # --- mark session closed --------------------------------------
    chat_id = SID_TO_SESSION.get(visitor_sid)
    if chat_id:
        chat = ChatSession.query.get(chat_id)
        if chat and chat.closed_at is None:
            chat.closed_at = datetime.utcnow()
            db.session.commit()

    # --- notify visitor -------------------------------------------
    emit("system", {"body": "This chat session has been closed by a representative. If you'd like to chat with us again, please open a new chat.",
                    "author": "system",
                    "ts": datetime.utcnow().isoformat(timespec="seconds")},
         room=visitor_sid)

    emit("chat_closed", {"chat_id": chat_id}, room=visitor_sid)

    # move visitor back to lobby if still online
    if visitor_sid in ALIVE:
        VISITORS.add(visitor_sid)
        emit("visitor_online",
             {"sid": visitor_sid,
              "username": SID_TO_NAME.get(visitor_sid)},
             room="reps")

    current_app.logger.debug("<<< rep left & closed chat", visitor_sid)

@socketio.on("satisfaction")
def save_rating(data):
    """
    Visitor clicked a 1-5 star rating after chat end.
    `data = { "score": 1-5 }`
    """
    score   = int(data.get("score", 0))
    chat_id = SID_TO_SESSION.get(request.sid)
    if not chat_id or not (1 <= score <= 5):
        return

    chat = ChatSession.query.get(chat_id)
    if chat and chat.rating is None:
        chat.rating = score
        db.session.commit()

@socketio.on("history_request")
@require_level(20)
def history_request(data):
    """Rep asks for the full history of one past chat."""
    chat_id = data.get("chat_id")
    if not chat_id:
        return

    messages = (Message.query
                .filter_by(chat_id=chat_id)
                .order_by(Message.ts)
                .all())

    emit("history_result", [
        {
            "body":   m.body,
            "author": m.author,
            "ts":     m.ts.isoformat(timespec="seconds")
        } for m in messages
    ], room=request.sid)

# ---------------------------------------------------------------------------
# Chat message flow
# ---------------------------------------------------------------------------
@socketio.on("visitor_msg")
def handle_visitor(text: str) -> None:
    """Handle a line typed by the visitor."""
    sid          = request.sid
    chat_id      = SID_TO_SESSION.get(sid)
    user_id      = SID_TO_USER.get(sid)
    visitor_name = SID_TO_NAME.get(sid, "Visitor")
    now          = datetime.utcnow()
    now_iso      = now.isoformat(timespec="seconds")
    off_hours    = is_off_hours()

    # ───────────────────────────────────────────────────────────────
    # 0) Waiting for description branch
    # ───────────────────────────────────────────────────────────────
    if sid in WAITING_DESC:
        WAITING_DESC.remove(sid)
        db.session.add(Message(chat_id=chat_id, author="visitor",
                               body=text, ts=now, user_id=user_id))

        if off_hours:
            reply = ("Thanks for the details! Our live chat is closed right now, "
                     "but we’ll review your message and e-mail you, typically by "
                     "the next business day.")
        else:
            reply = ("One of our representatives will be with you shortly.\n"
                     "Thank you for your patience.")
        emit("visitor_msg",
             {"body": reply, "author": "assistant", "ts": now_iso},
             room=sid)
        db.session.add(Message(chat_id=chat_id, author="assistant",
                               body=reply, ts=now, user_id=user_id))

        # Only wake reps if we’re inside office hours
        if not off_hours:
            NEW_CHATS.add(sid)
            emit("new_chat", {"sid": sid, "username": visitor_name},
                 room="reps")

        db.session.commit()
        return

    # ───────────────────────────────────────────────────────────────
    # 1) Quick-reply branch
    # ───────────────────────────────────────────────────────────────
    if text.startswith("__faq__:"):
        faq_id = text.split(":", 1)[1]

        # HUMAN / TALK-TO-REP
        if faq_id == "human":
            label = "Connect me to a representative"
            # 1. echo the visitor’s click so *they* see it
            emit("visitor_msg",
                 {"body": label, "author": "visitor", "ts": now_iso},
                 room=sid)

            # 2. choose the prompt (different after hours)
            if off_hours:
                prompt = ("Thanks for the details! Our live chat is closed right now, "
                          "but we’ll review your message and e-mail you, typically by "
                          "the next business day. If you aren't signed in, please leave "
                          "your email in the message. Thank you!")
            else:
                prompt = ("Before we connect you, can you briefly describe "
                          "what your question or concern is?")
                WAITING_DESC.add(sid)

            emit("visitor_msg",
                 {"body": prompt, "author": "assistant", "ts": now_iso},
                 room=sid)

            db.session.add_all([
                Message(chat_id=chat_id, author="visitor",
                        body=label, ts=now, user_id=user_id),
                Message(chat_id=chat_id, author="assistant",
                        body=prompt, ts=now, user_id=user_id)
            ])
            db.session.commit()
            return

        # every other FAQ shortcut
        try:
            label = FAQ[faq_id]["label"]
            answer = FAQ[faq_id]["answer"]
        except KeyError:
            current_app.logger.warning("Unknown FAQ id: %s", faq_id)
            return

        emit("visitor_msg",
             {"body": label, "author": "visitor", "ts": now_iso},
             room=sid)
        emit("visitor_msg",
             {"body": answer, "author": "assistant", "ts": now_iso},
             room=sid)

        db.session.add_all([
            Message(chat_id=chat_id, author="visitor",
                    body=label, ts=now, user_id=user_id),
            Message(chat_id=chat_id, author="assistant",
                    body=answer, ts=now, user_id=user_id)
        ])
        db.session.commit()
        return

    # ───────────────────────────────────────────────────────────────
    # 2) Standard free-text flow
    # ───────────────────────────────────────────────────────────────
    safe_body = clean(text)
    db.session.add(Message(chat_id=chat_id, author="visitor",
                           body=safe_body, ts=now, user_id=user_id))
    db.session.commit()

    # If a rep is already paired, forward immediately (even after hours)
    rep_sid = next((r for r, v in PAIR.items() if v == sid), None)
    if rep_sid:
        emit("visitor_msg",
             {"body": text, "author": "visitor", "ts": now_iso},
             room=rep_sid, include_self=False)
        return

    # Outside office hours we STOP here — the overnight query will pick
    # this chat up tomorrow.  During office hours we escalate as before.
    if off_hours:
        return

    # Escalate to NEW_CHATS because it’s office hours and no rep yet
    if sid in VISITORS:
        VISITORS.remove(sid)
        NEW_CHATS.add(sid)
        emit("visitor_offline", {"sid": sid}, room="reps")
        emit("new_chat",
             {"sid": sid, "username": visitor_name},
             room="reps")

@socketio.on("rep_msg")
@require_level(20)
def handle_rep(text: str) -> None:
    """Handle a line typed by the representative."""
    visitor_sid = PAIR.get(request.sid)
    chat_id = SID_TO_SESSION.get(visitor_sid)
    if chat_id is None:
        emit("system", "Chat session not found.", room=request.sid)
        return

    safe_body = clean(text)
    db.session.add(Message(chat_id=chat_id,
                           author="rep",
                           body=safe_body,
                           ts=datetime.utcnow(),
                           user_id=SID_TO_USER.get(request.sid)))
    db.session.commit()

    emit("rep_msg",
         {"body": text,
          "author": "rep",
          "ts": datetime.utcnow().isoformat(timespec="seconds")},
         room=visitor_sid, include_self=False)

@socketio.on("typing")
def visitor_typing(data):
    rep_sid = next((r for r, v in PAIR.items() if v == request.sid), None)
    if rep_sid:
        emit("typing",
             {"sid": request.sid, "is_typing": data["is_typing"]},
             room=rep_sid, include_self=False)

# rep → visitor
@socketio.on("rep_typing")
def rep_typing(data):
    visitor_sid = PAIR.get(request.sid)
    if visitor_sid:
        emit("rep_typing",
             {"is_typing": data["is_typing"]},
             room=visitor_sid, include_self=False)