# flask_app/tests/test_chat.py

def test_visitor_to_server_roundtrip(visitor_and_rep):
    visitor, rep = visitor_and_rep

    visitor.emit("visitor_msg", "hello")
    packets = rep.get_received()

    assert any(p["name"] == "visitor_msg" and p["args"][0] == "hello"
               for p in packets)

def test_first_message_queues_chat(visitor_and_rep):
    visitor, rep = visitor_and_rep

    visitor.emit("visitor_msg", "hello")
    events = rep.get_received()

    names = [pkt["name"] for pkt in events]
    assert "new_chat" in names