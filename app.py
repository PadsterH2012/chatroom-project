import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_socketio import SocketIO, emit, join_room, leave_room  # Import emit here

# Add the root directory of your project to the Python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from models import db, User
from routes import register_blueprints

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'

csrf = CSRFProtect(app)

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

from socketio_instance import socketio  # Import socketio instance from the new module
socketio.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))  # Updated for SQLAlchemy 2.0

with app.app_context():
    db.create_all()

register_blueprints(app)  # Register blueprints after all routes are imported

@socketio.on('connect', namespace='/progress')
def connect():
    print('Client connected')
    emit('progress', {'status': 'Connected to server'})

@socketio.on('disconnect', namespace='/progress')
def disconnect():
    print('Client disconnected')

if __name__ == "__main__":
    socketio.run(app, debug=True)
