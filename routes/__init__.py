from flask import Blueprint, render_template

# Define the home blueprint
home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def home():
    return render_template('home.html')

def register_blueprints(app):
    from .auth_routes import auth_bp
    from .chat_routes import chat_bp
    from .project_routes import project_bp
    from .settings_routes import settings_bp
    from .agent_routes import agent_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(chat_bp, url_prefix='/chat')
    app.register_blueprint(project_bp, url_prefix='/project')
    app.register_blueprint(settings_bp, url_prefix='/settings')
    app.register_blueprint(agent_bp, url_prefix='/agents')
    app.register_blueprint(home_bp)  # Register the home blueprint
