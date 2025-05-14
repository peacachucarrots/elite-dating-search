# app/chat/routes.py
"""
Live-chat blueprint: HTTP view for /rep plus all Socket.IO event handlers.
All in-memory state lives here (ALIVE, VISITORS, etc.). Swap for a DB later.
"""

from collections import defaultdict

from flask import Blueprint, render_template, request
from flask_socketio import emit, join_room, leave_room

from app.extensions import socketio
from . import bp

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
PAIR: dict[str, str]     = {}             # rep_sid ➜ visitor_sid
BACKLOG = defaultdict(list)               # visitor_sid ➜ [queued lines]

# ---------------------------------------------------------------------------
# Socket.IO lifecycle
# ---------------------------------------------------------------------------
@socketio.on("connect")
def handle_connect():
    ALIVE.add(request.sid)
    VISITORS.add(request.sid)
    join_room(request.sid)                        # personal room
    emit("visitor_online", {"sid": request.sid}, room="reps")
    print("+++ connect", request.sid)

@socketio.on("disconnect")
def handle_disconnect():
    ALIVE.discard(request.sid)
    VISITORS.discard(request.sid)
    NEW_CHATS.discard(request.sid)

    # If a rep closes, notify their visitor
    visitor_sid = PAIR.pop(request.sid, None)
    if visitor_sid:
        emit("system", "Representative disconnected.", room=visitor_sid)

    emit("visitor_offline", {"sid": request.sid}, room="reps")
    print("--- disconnect", request.sid)

# ---------------------------------------------------------------------------
# Rep dashboard actions
# ---------------------------------------------------------------------------
@socketio.on("iam_rep")
def mark_rep():
    # Remove this socket from visitor pool
    if request.sid in VISITORS:
        VISITORS.discard(request.sid)
        emit("visitor_offline", {"sid": request.sid}, room="reps")

    join_room("reps")      # add to reps room

    # Send current visitor list only to this rep
    for v in VISITORS:
        emit("visitor_online", {"sid": v}, room=request.sid)

@socketio.on("join_visitor")
def join_visitor(data):
    visitor_sid = data["sid"]

    # Validate selection
    if visitor_sid not in VISITORS and visitor_sid not in NEW_CHATS:
        emit("system", "Visitor is no longer online.", room=request.sid)
        return

    PAIR[request.sid] = visitor_sid

    # replay queued lines
    for line in BACKLOG.pop(visitor_sid, []):
        emit("visitor_msg", line, room=request.sid)

    # clean up lists
    VISITORS.discard(visitor_sid)
    if visitor_sid in NEW_CHATS:
        NEW_CHATS.remove(visitor_sid)
        emit("new_chat_remove", {"sid": visitor_sid}, room="reps")

    emit("system", "Representative joined the chat", room=visitor_sid)
    print("### rep picked", visitor_sid)

@socketio.on("leave_visitor")
def leave_visitor(data):
    visitor_sid = data["sid"]

    # break pairing
    if PAIR.get(request.sid) == visitor_sid:
        del PAIR[request.sid]
    leave_room(visitor_sid)

    # return visitor to lobby if still connected
    if visitor_sid in ALIVE:
        VISITORS.add(visitor_sid)
        emit("visitor_online", {"sid": visitor_sid}, room="reps")

    emit("system", "Representative has left the chat.", room=visitor_sid)
    print("<<< rep left", visitor_sid)

# ---------------------------------------------------------------------------
# Chat message flow
# ---------------------------------------------------------------------------
@socketio.on("visitor_msg")
def handle_visitor(msg):
    rep_sid = next((rep for rep, vis in PAIR.items()
                    if vis == request.sid), None)

    if rep_sid:
        # paired → forward straight to the rep
        emit("visitor_msg", msg, room=rep_sid, include_self=False)
        return

    # ── visitor not paired ──
    BACKLOG[request.sid].append(msg)           # queue it

    if len(BACKLOG[request.sid]) == 1:         # ← first ever message
        VISITORS.discard(request.sid)
        NEW_CHATS.add(request.sid)

        emit("visitor_offline", {"sid": request.sid}, room="reps")
        emit("new_chat",        {"sid": request.sid}, room="reps")
        emit("system",
             "One of our representatives will be with you shortly.",
             room=request.sid)
    # for 2nd, 3rd … messages we just keep stacking the backlog

@socketio.on("rep_msg")
def handle_rep(msg):
    visitor_sid = PAIR.get(request.sid)
    if visitor_sid:
        emit("rep_msg", msg, room=visitor_sid, include_self=False)
    else:
        emit("system", "Select a visitor first.", room=request.sid)