import pytest

from app import create_app, db
from app.models import User, ChatSession, Message


@pytest.fixture()
def app():
    """Create and configure a new app instance for each test."""
    test_app = create_app()  # uses settings.Test (inherits in‑memory DB)
    test_app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,      # forms shouldn’t require CSRF tokens in unit tests
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
    )

    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    """Flask test client bound to the fresh app instance."""
    return app.test_client()


def _create_dummy_users():
    """Return a (visitor, rep) pair persisted to the DB."""
    visitor = User(email="visitor@example.com", pw_hash="x")
    rep     = User(email="rep@example.com",     pw_hash="x")
    db.session.add_all([visitor, rep])
    db.session.commit()
    return visitor, rep


def test_message_persistence(app):
    """A `Message` row should be written when we add it to a session."""
    with app.app_context():
        visitor, _ = _create_dummy_users()

        # 1️⃣ open a chat session (normally done in Socket.IO on connect)
        chat = ChatSession(visitor=visitor)
        db.session.add(chat)
        db.session.commit()

        # 2️⃣ visitor sends a message
        msg_body = "Hello, world!"
        msg = Message(session=chat, sender_role="visitor", body=msg_body)
        db.session.add(msg)
        db.session.commit()

        # 3️⃣ ASSERTIONS ------------------------------------------------------
        assert Message.query.count() == 1
        saved = Message.query.first()
        assert saved.body == msg_body
        assert saved.sender_role == "visitor"
        assert saved.session_id == chat.id
