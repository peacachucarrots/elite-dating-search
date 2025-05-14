# flask_app/tests/test_chat.py
from flask_app import create_app, socketio

def test_visitor_to_server_roundtrip():
    app = create_app()

    # give the test client its own socket connection
    client = socketio.test_client(app)

    assert client.is_connected()

    # 1️⃣  emit from “browser” → server
    client.emit("visitor_msg", "hello test")

    # 2️⃣  grab everything the server emitted back
    received = client.get_received()

    # optional sanity print
    # print(received)

    # expect a rep_msg echo (because our handler echoes or broadcasts)
    names = [pkt["name"] for pkt in received]
    assert "rep_msg" in names

def test_first_message_queues_chat(visitor_and_rep):
    visitor, rep = visitor_and_rep

    visitor.emit("visitor_msg", "hello")
    events = rep.get_received()

    names = [pkt["name"] for pkt in events]
    assert "new_chat" in names