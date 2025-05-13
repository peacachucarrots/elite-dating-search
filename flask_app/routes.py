from flask import Blueprint, render_template, url_for, abort, session, request
from flask_socketio import emit, join_room, leave_room
from . import socketio
from .blog_posts import POSTS

from collections import defaultdict
BACKLOG = defaultdict(list)

main = Blueprint("main", __name__)

@main.route("/")
def index():
    posts = [
        {
            "title": "Dating With Intention",
            "slug":  "dating-with-intention",
            "img":   url_for("static", filename="img/blog/thumb_dating.jpg")
        },
        {
            "title": "Executive Search—for Love",
            "slug":  "executive-search-for-love",
            "img":   url_for("static", filename="img/blog/thumb_exec.jpg")
        },
        {
            "title": "Ready for Matchmaker",
            "slug": "ready-for-matchmaker",
            "img": url_for("static", filename="img/blog/thumb_ready.jpg")
        },
        {
            "title": "First Date Chemistry",
            "slug": "first-date-chemistry",
            "img": url_for("static", filename="img/blog/thumb_chem.jpg")
        },
    ]

    for p in posts:
        p["url"] = url_for("blog.show_post", slug=p["slug"])

    return render_template("index.html", recent_posts=posts)

@main.route("/matchmaking-services")
def matchmaking_services():
    return render_template("matchmaking_services.html")

@main.route('/our-process')
def our_process():
    return render_template('our_process.html')

@main.route("/roi-of-love")
def roi_of_love():
    return render_template("roi_of_love.html")

@main.route("/testimonials")
def testimonials():
    # Supply a list of testimonial dicts to the template
    data = [
        {"name": "Dave & Rebecca", "quote": "I can honestly say ...", "image": "img/testimonials/dave_rebecca.jpg"},
        # ...
    ]
    return render_template("testimonials.html", testimonials=data)

@main.route("/about-us")
def about_us():
    return render_template("about_us.html")

@main.route("/get-started")
def get_started():
    return render_template("get_started.html")

@main.route("/save-candidate")
def save_candidate():
    return render_template("save_candidate.html")

@main.route("/candidate-program")
def candidate_program():
    return render_template("candidate_program.html")

@main.route("/client-program")
def client_program():
    return render_template("client_program.html")

blog = Blueprint("blog",
                 __name__,
                 url_prefix="/blog")    # /blog/<slug>

# one route that serves *any* post in the list
@blog.route("/<slug>")
def show_post(slug):
    # 404 if slug is not in POST list
    if slug not in {p["slug"] for p in POSTS}:
        abort(404)
    return render_template(f"blog/{slug}.html")

# --- LIVE CHAT --- #

ALIVE: set[str] = set()         # sockets that are still open
VISITORS: set[str]   = set()    # active visitor socket-IDs
NEW_CHATS: set[str]  = set()    # messaged but unpaired
PAIR: dict[str, str] = {}       # rep_sid ➜ visitor_sid

# ── HTTP ─────────────────────────────────────────────────────────────────────
@main.route("/rep")
def rep_dashboard():
    return render_template("chat/rep.html")

# ── SOCKET: CONNECT / DISCONNECT ─────────────────────────────────────────────
@socketio.on("connect")
def handle_connect():
    ALIVE.add(request.sid)
    VISITORS.add(request.sid)
    join_room(request.sid)
    emit("visitor_online", {"sid": request.sid}, room="reps")
    print("+++ connect", request.sid)

@socketio.on("disconnect")
def handle_disconnect():
    ALIVE.discard(request.sid)
    VISITORS.discard(request.sid)
    NEW_CHATS.discard(request.sid)

    # If this was a paired rep, un-pair and notify visitor
    visitor_sid = PAIR.pop(request.sid, None)
    if visitor_sid:
        emit("system", "Representative disconnected.", room=visitor_sid)

    emit("visitor_offline", {"sid": request.sid}, room="reps")
    print("--- disconnect", request.sid)

@socketio.on("leave_visitor")
def leave_visitor(data):
    visitor_sid = data["sid"]

    # break pairing
    if PAIR.get(request.sid) == visitor_sid:
        del PAIR[request.sid]
    leave_room(visitor_sid)

    # put visitor back in lobby **only if they’re still connected**
    if visitor_sid in ALIVE:
        VISITORS.add(visitor_sid)
        emit("visitor_online", {"sid": visitor_sid}, room="reps")

    emit("system", "Representative has left the chat.", room=visitor_sid)
    print("<<< rep left", visitor_sid)

# ── SOCKET: REP IDENTIFIES AND PICKS A VISITOR ───────────────────────────────
@socketio.on("iam_rep")
def mark_rep():
    if request.sid in VISITORS:
        VISITORS.discard(request.sid)
        emit("visitor_offline", {"sid": request.sid}, room="reps")  # NEW

    join_room("reps")

    # replay backlog just to this rep
    for v in VISITORS:
        emit("visitor_online", {"sid": v}, room=request.sid)

@socketio.on("join_visitor")
def join_visitor(data):
    visitor_sid = data["sid"]
    if visitor_sid not in VISITORS and visitor_sid not in NEW_CHATS:
        emit("system", "Visitor is no longer online.", room=request.sid)
        return

    PAIR[request.sid] = visitor_sid

    # replay backlog
    for line in BACKLOG.pop(visitor_sid, []):
        emit("visitor_msg", line, room=request.sid)

    # clean up lists
    VISITORS.discard(visitor_sid)
    if visitor_sid in NEW_CHATS:
        NEW_CHATS.remove(visitor_sid)
        emit("new_chat_remove", {"sid": visitor_sid}, room="reps")

    emit("system", "Rep joined the chat", room=visitor_sid)
    print("### rep picked", visitor_sid)

# ── SOCKET: CHAT MESSAGES ────────────────────────────────────────────────────
@socketio.on("visitor_msg")
def handle_visitor(msg):
    rep_sid = next((rep for rep, vis in PAIR.items()
                    if vis == request.sid), None)

    if rep_sid:
        # already paired → forward live
        emit("visitor_msg", msg, room=rep_sid, include_self=False)
    else:
        # queue it for later
        BACKLOG[request.sid].append(msg)

        # first time? move to new-chat list as before
        if request.sid in VISITORS:
            VISITORS.remove(request.sid)
            NEW_CHATS.add(request.sid)
            emit("visitor_offline", {"sid": request.sid}, room="reps")
            emit("new_chat",        {"sid": request.sid}, room="reps")

        # courtesy ack
        emit("system", "One of our representatives will be with you shortly.",
             room=request.sid)

@socketio.on("rep_msg")
def handle_rep(msg):
    visitor_sid = PAIR.get(request.sid)
    if visitor_sid:
        # NOTE: emit rep_msg, not visitor_msg
        emit("rep_msg", msg, room=visitor_sid, include_self=False)
    else:
        emit("system", "⚠︎ Select a visitor first.", room=request.sid)