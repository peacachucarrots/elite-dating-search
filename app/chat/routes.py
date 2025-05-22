# app/chat/routes.py
"""
Live-chat blueprint: HTTP view for /rep plus all Socket.IO event handlers.
All in-memory state lives here (ALIVE, VISITORS, etc.). Swap for a DB later.
"""

from collections import defaultdict
from datetime import datetime

from flask import Blueprint, render_template, request
from flask_socketio import emit, join_room, leave_room
from flask_login import current_user, logout_user

from sqlalchemy import func

from app.extensions import socketio, db
from app.models.chat import ChatSession, Message
from . import bp

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def _get_session(visitor_sid) -> ChatSession:
    sess = ChatSession.query.filter_by(id=visitor_sid).first()
    if not sess:
        sess = ChatSession(id=visitor_sid,
                           visitor_id=current_user.get_id() if current_user.is_authenticated else None)
        db.session.add(sess)
        db.session.commit()
    return sess

def _create_session_for(user_id: int) -> ChatSession:
    next_seq = (db.session.query(func.coalesce(func.max(ChatSession.seq), 0))
                .filter_by(user_id=user_id)
                .scalar()) + 1
    chat = ChatSession(user_id=user_id, seq=next_seq)
    db.session.add(chat)
    db.session.commit()
    return chat

# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------
@bp.route("/rep")
def rep_dashboard():
    """Representative dashboard (lists visitors + chat panel)."""
    return render_template("rep.html")

# ---------------------------------------------------------------------------
# In-memory state (replace with DB when needed)
# ---------------------------------------------------------------------------
ALIVE: set[str]          = set()          # sockets currently connected
VISITORS: set[str]       = set()          # idle visitors
NEW_CHATS: set[str]      = set()          # visitors who sent 1st msg
REPS: set[str]           = set()
PAIR: dict[str, str]     = {}             # rep_sid ➜ visitor_sid
SID_TO_USER              = {}             # visitor_sid ➜ user.id
SID_TO_NAME              = {}             # visitor_sid ➜ display_name
SID_TO_SESSION           = {}             # visitor_sid ➜ chat.id

# ---------------------------------------------------------------------------
# Socket.IO lifecycle
# ---------------------------------------------------------------------------
# app/chat/routes.py
@socketio.on("connect")
def handle_connect():
    if not current_user.is_authenticated:
        emit("system",
             {"body": "Please log in to use the chat.",
             "author": "system",
             "ts": datetime.utcnow().isoformat(timespec='seconds')},
             room=request.sid)
        handle_disconnect()
        return

    role = request.args.get("role", "visitor")
    ALIVE.add(request.sid)

    user_id      = current_user.id
    display_name = current_user.display_name or current_user.email.split("@")[0]

    SID_TO_USER[request.sid] = user_id
    SID_TO_NAME[request.sid] = display_name

    match role:
        case "visitor":
            chat = (ChatSession.query
                    .filter_by(user_id=user_id, closed_at=None)
                    .order_by(ChatSession.opened_at.desc())
                    .first())

            if chat is None:
                chat = _create_session_for(user_id)

            SID_TO_SESSION[request.sid] = chat.id

            VISITORS.add(request.sid)
            join_room(request.sid)

            history = (Message.query
                       .filter_by(chat_id=chat.id)
                       .order_by(Message.ts)
                       .all())

            for m in history:
                emit("visitor_msg",
                     {"body": m.body,
                      "author": m.author,
                      "ts": m.ts.isoformat()},
                     room=request.sid)

            emit("visitor_online",
                 {"sid": request.sid, "username": display_name},
                 room="reps")
            print("+++ Visitor connected", display_name)
            return
        case "rep":
            REPS.add(request.sid)
            join_room("reps")
            print("+++ REP connected", display_name)
            return
        case _:
            print(f"!!! Unknown role '{role}' for SID {request.sid}. Treating as a visitor...")
            VISITORS.add(request.sid)
            join_room(request.sid)
            emit("visitor_online", {"sid": request.sid}, room="reps")
            print("+++ Unknown Role connected", request.sid)

from datetime import datetime

@socketio.on("disconnect")
def handle_disconnect():
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

    print("--- disconnect", username or sid)

# ---------------------------------------------------------------------------
# Rep dashboard actions
# ---------------------------------------------------------------------------
@socketio.on("iam_rep")
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

@socketio.on("join_visitor")
def join_visitor(data):
    """Rep dashboard requests to handle a specific visitor SID."""
    visitor_sid = data["sid"]
    rep_sid     = request.sid

    user_id = SID_TO_USER.get(visitor_sid)
    chat_id = SID_TO_SESSION[visitor_sid]

    sessions = (ChatSession.query
                .filter(ChatSession.user_id == user_id,
                        ChatSession.id != chat_id,
                        ChatSession.closed_at.isnot(None))
                .order_by(ChatSession.opened_at.desc())
                .all())

    emit("session_list", [
        {
            "chat_id": s.id,
            "label": f"{s.seq:04d}",
            "opened": s.opened_at.isoformat(timespec="seconds"),
            "closed": s.closed_at.isoformat(timespec="seconds")
        }
        for s in sessions
    ], room=rep_sid)

    if visitor_sid not in VISITORS and visitor_sid not in NEW_CHATS:
        emit("system",
             {"body": "Visitor is no longer online.",
              "author": "system",
              "ts": datetime.utcnow().isoformat(timespec="seconds")},
             room=rep_sid)
        return

    PAIR[rep_sid] = visitor_sid
    join_room(visitor_sid)

    rep_name = SID_TO_NAME.get(rep_sid, "Representative")
    emit("system",
         {"body": f"{rep_name} has joined the chat.",
                "author": "system",
                "ts": datetime.utcnow().isoformat(timespec="seconds")},
            room=visitor_sid)

    emit("system",
         {"body": f"You joined {SID_TO_NAME.get(visitor_sid, visitor_sid[:8])}",
                "author": "system",
                "ts": datetime.utcnow().isoformat(timespec="seconds")},
            room=rep_sid)

    # ── 1 · replay db history ────────────────────────────────────────────
    history = (Message.query
               .filter_by(chat_id=chat_id)
               .order_by(Message.ts)
               .all())

    for m in history:
        emit("visitor_msg",
             {"body": m.body,
              "author": m.author,
              "ts": m.ts.isoformat()},
             room=rep_sid)

    VISITORS.discard(visitor_sid)
    NEW_CHATS.discard(visitor_sid)
    emit("new_chat_remove", {"sid": visitor_sid}, room="reps")

    emit("live_chat_ready", room=rep_sid)

    print(f"### rep {rep_sid[:8]} paired with visitor {visitor_sid[:8]}")

@socketio.on("leave_visitor")
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

    # ── Tell the visitor ───────────────────────────────────────────────────────
    rep_name = SID_TO_NAME.get(rep_sid, "Representative")
    emit("system",
         {"body": f"{rep_name} has left the chat.",
          "author": "system",
          "ts": datetime.utcnow().isoformat(timespec="seconds")},
         room=visitor_sid)

    # ── If the visitor tab is still open, return them to the idle list ─────────
    if visitor_sid in ALIVE:
        VISITORS.add(visitor_sid)
        emit("visitor_online",
             {"sid": visitor_sid,
              "username": SID_TO_NAME.get(visitor_sid)},
             room="reps")

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

    print("<<< rep left", visitor_sid)

@socketio.on("history_request")
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
    chat_id = SID_TO_SESSION[request.sid]
    user_id = SID_TO_USER[request.sid]

    db.session.add(Message(chat_id=chat_id,
                           author="visitor",
                           body=text,
                           ts=datetime.utcnow(),
                           user_id=user_id
                           ))
    db.session.commit()

    packet = {"body": text,
              "author": "visitor",
              "ts": datetime.utcnow().isoformat(timespec="seconds")}

    rep_sid = next((r for r, v in PAIR.items() if v == request.sid), None)

    if rep_sid:
        emit("visitor_msg", packet, room=request.sid)
        return

    if request.sid in VISITORS:
        NEW_CHATS.add(request.sid)
        emit("visitor_offline", {"sid": request.sid}, room="reps")
        emit("new_chat",        {"sid": request.sid, "username": SID_TO_NAME[request.sid]}, room="reps")

@socketio.on("rep_msg")
def handle_rep(text: str) -> None:
    """Handle a line typed by the representative."""
    visitor_sid = PAIR.get(request.sid)
    if not visitor_sid:
        emit("system", "Select a visitor first.", room=request.sid)
        return

    chat_id = SID_TO_SESSION.get(visitor_sid)
    if chat_id is None:
        emit("system", "Chat session not found.", room=request.sid)
        return

    db.session.add(Message(chat_id=chat_id,
                           author="rep",
                           body=text,
                           ts=datetime.utcnow(),
                           user_id=SID_TO_USER.get(request.sid)))
    db.session.commit()

    emit("rep_msg",
         {"body": text,
          "author": "rep",
          "ts": datetime.utcnow().isoformat(timespec="seconds")},
         room=visitor_sid, include_self=False)