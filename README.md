# Elite Dating Search – Real-time Concierge Chat

A Flask + Socket.IO web app that lets high-end dating clients chat with live
representatives instantly—no signup, no page reloads.

---

## Features
- **Real-time visitor → representative chat** (WebSockets).
- Reps see *Active Visitors* and *New Chats* queues.
- System messages & typing indicators.
- In-memory matchmaking; pluggable for database later.
- Container-ready (`docker compose up`) with Eventlet web server.

---

## Tech Stack
| Layer | Tech |
|-------|------|
| Backend | Flask 2, Flask-SocketIO 5 (Eventlet) |
| Frontend | Vanilla JS, TailwindCSS |
| Testing | Pytest + Flask-SocketIO’s test client |
| Deployment | Docker, Gunicorn-eventlet |

---

## Getting Started

### Prerequisites
bash
python 3.12+
git
# optional: Docker 24+ for container workflow