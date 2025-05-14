"""
Singleton instances of Flask extensions.
Import these wherever you need them, then call
`socketio.init_app(app)` inside create_app().
"""

from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail

# CORS is left wide-open for now; tighten in production.
socketio = SocketIO(cors_allowed_origins="*")
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"         # redirect for @login_required
login_manager.session_protection = "strong"
migrate = Migrate()
mail = Mail()

# ----------------------------------------------------------------------
# Ready for future extensions — just uncomment / install when needed.
# ----------------------------------------------------------------------
# from flask_sqlalchemy import SQLAlchemy
# db = SQLAlchemy()
#
# from flask_migrate import Migrate
# migrate = Migrate()
#
# from flask_bcrypt import Bcrypt
# bcrypt = Bcrypt()