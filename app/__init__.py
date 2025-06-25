app/__init__.py
"""
Application factory + blueprint registration.
Call create_app() from run.py, tests, or your WSGI entry-point.
"""

from __future__ import annotations

import os
import calendar
from datetime import datetime
from importlib import import_module
from typing import Union

from flask import Flask, url_for, current_app
from werkzeug.middleware.proxy_fix import ProxyFix

# ── Extensions (one singleton each) ────────────────────────────────
from app.extensions import (
    db,
    migrate,
    mail,
    socketio,
    login_manager,
    csrf,
    limiter,
)

# Optional security extras
# from flask_talisman import Talisman

# ------------------------------------------------------------------
# Configuration loader
# ------------------------------------------------------------------
DEFAULT_SETTINGS = "app.settings.Dev"

def _load_config(app: Flask, cfg: Union[str, type, None]) -> None:
    """
    Accepts:
    • dotted-path string   -> "package.module.Class"
    • class / object       -> Config class instance
    • None                 -> DEFAULT_SETTINGS
    """
    if cfg is None:
        cfg = os.getenv("FLASK_CONFIG", DEFAULT_SETTINGS)

    if isinstance(cfg, str):
        module_path, _, class_name = cfg.rpartition(".")
        cfg_obj = getattr(import_module(module_path), class_name)
    else:
        cfg_obj = cfg

    app.config.from_object(cfg_obj)

def dated_url_for(endpoint, **values):
    if endpoint == "static" or endpoint.endswith(".static"):
        # resolves the correct static folder (app or blueprint)
        folder = (current_app.static_folder if endpoint == "static"
                  else current_app.blueprints[endpoint.rsplit(".", 1)[0]].static_folder)
        filename = values.get("filename")
        if filename:
            try:
                values["v"] = int(os.stat(os.path.join(folder, filename)).st_mtime)
            except OSError:
                pass  # file missing: skip cache-buster
    return url_for(endpoint, **values)


# ------------------------------------------------------------------
# Factory
# ------------------------------------------------------------------
def create_app(config_object: Union[str, type, None] = None) -> Flask:
    app = Flask(__name__, static_url_path="/static")
    _load_config(app, config_object)

    # ── Bind extensions ────────────────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    app.jinja_env.globals["url_for"] = dated_url_for
    # ── User loader for Flask-Login ────────────────────────────────
    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id: str) -> User | None:
        return User.query.get(int(user_id))

    # ── Blueprints ────────────────────────────────────────────────
    from .main import bp as main_bp
    from .admin import bp as admin_bp
    from .chat import bp as chat_bp
    from .blog import bp as blog_bp
    from .auth import bp as auth_bp
    from .program import bp as program_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(chat_bp, url_prefix="/chat")
    app.register_blueprint(blog_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(program_bp, url_prefix="/program")

    # ── Security headers (prod) ───────────────────────────────────
    # if not app.debug:
    #     csp = {
    #         "default-src": ["'self'"],
    #         "script-src": ["'self'", "https://js.stripe.com"],
    #         "style-src":  ["'self'", "https://cdn.jsdelivr.net"],
    #         "img-src":    ["'self'", "data:"],
    #     }
    #     Talisman(
    #         app,
    #         content_security_policy=csp,
    #         content_security_policy_nonce_in=["script"],
    #         force_https=True,
    #         frame_options="DENY",
    #     )

    # ── Trust reverse-proxy headers (NGINX → Gunicorn) ────────────
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    # ── Jinja globals & filters ───────────────────────────────────
    @app.context_processor
    def inject_now() -> dict[str, int]:
        return {"current_year": datetime.utcnow().year}

    @app.template_filter("month_name")
    def month_name(value) -> str:
        return calendar.month_name[int(value)]

    # ── CLI commands (Flask-Migrate, etc.) ───────────────────────
    from .cli import register_commands

    register_commands(app)

    return app
