from flask import Flask
from flask_socketio import SocketIO
from datetime import datetime
import calendar

# socketio = SocketIO(cors_allowed_origins="*", message_queue="redis://")
socketio = SocketIO(cors_allowed_origins="*")

def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = "dev"
    socketio.init_app(app)

    from .routes import main
    app.register_blueprint(main)
    from .routes import blog
    app.register_blueprint(blog)

    @app.context_processor
    def inject_now():
        return {"current_year": datetime.utcnow().year}

    @app.template_filter('month_name')
    def month_name(value):
        """Convert an int 1-12 to ‘January’-‘December’."""
        return calendar.month_name[int(value)]

    return app
