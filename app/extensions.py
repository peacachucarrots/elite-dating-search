"""
Singleton instances of Flask extensions.
Import these wherever you need them, then call
`socketio.init_app(app)` inside create_app().
"""

from flask_wtf import CSRFProtect
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os

convention = {
    "ix":  "ix_%(column_0_label)s",
    "uq":  "uq_%(table_name)s_%(column_0_name)s",
    "ck":  "ck_%(table_name)s_%(constraint_name)s",
    "fk":  "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk":  "pk_%(table_name)s"
}

socketio = SocketIO(cors_allowed_origins="*")
db = SQLAlchemy(metadata=MetaData(naming_convention=convention))
login_manager = LoginManager()
login_manager.login_view = "auth.login"         # redirect for @login_required
login_manager.session_protection = "strong"
migrate = Migrate()
mail = Mail()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, storage_uri=os.environ.get("LIMITER_STORAGE_URI"))

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
