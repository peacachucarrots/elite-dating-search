# tests/conftest.py
import pytest
from app import create_app
from app.extensions import socketio as _socketio


@pytest.fixture(scope="session")
def app():
    """Return a Flask app configured for tests."""
    _app = create_app("app.settings.Dev")
    # override config here if needed, e.g. in-mem DB URI
    _app.config["TESTING"] = True
    return _app


@pytest.fixture(scope="function")
def socketio_client(app):
    """
    Give each test its *own* Socket.IO test client,
    automatically connected to the `app` context.
    """
    client = _socketio.test_client(app)
    yield client
    client.disconnect()


# convenience fixture: pair of visitor + rep clients
@pytest.fixture(scope="function")
def visitor_and_rep(app):
    visitor = _socketio.test_client(app)          # tab 1
    rep     = _socketio.test_client(app)          # tab 2 (will call iam_rep)

    # mark second socket as rep
    rep.emit("iam_rep")
    rep.get_received()      # clear handshake packets

    yield visitor, rep

    visitor.disconnect()
    rep.disconnect()