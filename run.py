from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(".env"))
load_dotenv(Path(".env.dev"), override=True)

from app import create_app
from app.extensions import socketio

app = create_app()

if __name__ == "__main__":
    socketio.run(app, host="127.0.0.1", port=8080, debug=True, allow_unsafe_werkzeug=True)