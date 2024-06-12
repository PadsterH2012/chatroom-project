from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from models import db, User
from routes import register_blueprints
from flask_wtf.csrf import CSRFProtect

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

@login_manager.user_loader
def load_user(user_id):
    with db.session() as session:
        return session.get(User, int(user_id))

with app.app_context():
    db.create_all()

register_blueprints(app)

if __name__ == "__main__":
    app.run(debug=True)
