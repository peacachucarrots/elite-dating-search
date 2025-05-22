# tests/conftest.py
import pytest
from app import create_app
from app.extensions import db as _db, socketio as _socketio


# ──────────────────────────────────────────────────────────────
# 1️⃣  Build one application per *test function* so we always get
#     a brand-new in-memory database.
# ──────────────────────────────────────────────────────────────
@pytest.fixture(scope="function")
def app():
    app = create_app("app.settings.Test")          # -> sqlite:///:memory:
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_ENGINE_OPTIONS={"future": True},
    )

    with app.app_context():
        _db.create_all()           # ← create the tables

    yield app                      # test runs here

    # clean-up: drop everything and remove session
    with app.app_context():
        _db.session.remove()
        _db.drop_all()


# ──────────────────────────────────────────────────────────────
# 2️⃣  Give every test its own Socket.IO clients that depend on
#     the *app* fixture (tables exist by then).
# ──────────────────────────────────────────────────────────────
@pytest.fixture
def socketio_client(app):          #  ← depends on *app*
    client = _socketio.test_client(app)
    yield client
    client.disconnect()


@pytest.fixture
def visitor_and_rep(app):
    visitor = _socketio.test_client(app)
    rep     = _socketio.test_client(app)
    rep.emit("iam_rep"); rep.get_received()
    yield visitor, rep
    visitor.disconnect(); rep.disconnect()