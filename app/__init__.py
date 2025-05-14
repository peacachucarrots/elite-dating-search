# app/__init__.py
"""
Application factory + blueprint registration.
Call create_app() from run.py, tests, or a WSGI entrypoint.
"""

from datetime import datetime
import calendar
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from app.models import db
from .settings import Dev, Prod
from .extensions import socketio, db, login_manager, migrate, mail


def create_app():
    """Create and configure a Flask application instance."""
    app = Flask(__name__)
    app.config.from_object("app.settings.Dev")

    # ── Init extensions ─────────────────────────────────────────────
    socketio.init_app(app, cors_allowed_origins="*")
    mail.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id: str) -> User | None:
        return User.query.get(int(user_id))

    # ── Register blueprints ─────────────────────────────────────────
    from .main import bp as main_bp
    from .chat import bp as chat_bp
    from .blog import bp as blog_bp
    from .auth import bp as auth_bp

    app.register_blueprint(main_bp)               # /
    app.register_blueprint(chat_bp, url_prefix="/chat")   # /chat/…
    app.register_blueprint(blog_bp)               # /blog/<slug>
    app.register_blueprint(auth_bp, url_prefix="/auth")

    # ── Global context + filters ───────────────────────────────────
    @app.context_processor
    def inject_now():
        return {"current_year": datetime.utcnow().year}

    @app.template_filter("month_name")
    def month_name(value):
        """Convert int 1-12 to 'January'-'December'."""
        return calendar.month_name[int(value)]

    return app