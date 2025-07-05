# Elite Dating Search – Real-time Concierge Chat

A Flask + Socket.IO web app that lets high-end dating clients chat with live
representatives.

---

## Features
- **Real-time visitor → representative chat** (WebSockets).
- Reps see *Active Visitors* and *New Chats* queues.
- System messages & typing indicators.
- Container-ready with gevent web server.

---

## Tech Stack
| Layer | Tech |
|-------|------|
| Backend | Flask 2, Flask-SocketIO (gevent) |
| Frontend | CSS, JS |
| Testing | Pytest + Flask-SocketIO’s test client |
| Deployment | Docker, Gunicorn |

---

## Getting Started
To get this web application running on the web, first download a copy to your 
local machine's droplet. You'll then need to build and deploy the application 
using docker commands. Ensure you have all prerequisites installed beforehand.

## Prerequisites
- bash
- python 3.12+
- git
- Docker 24+
- Postgresql 16

> ## TODO:
- Don't require people to log in to chat.
- Don't require people to log in to fill out a client or application form.

Later: Pick either global tailwind css or individual stylesheets and stick to one plan.
