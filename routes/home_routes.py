from flask import Blueprint, render_template

# Define the home blueprint
home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def home():
    return render_template('project_room.html')