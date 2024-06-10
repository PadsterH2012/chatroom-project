from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    password = db.Column(db.String(128))
    role = db.Column(db.String(20))

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    objectives = db.Column(db.Text, nullable=True)
    goals = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)

    def __init__(self, name, description=None, objectives=None, goals=None, start_date=None, end_date=None):
        self.name = name
        self.description = description
        self.objectives = objectives
        self.goals = goals
        self.start_date = start_date
        self.end_date = end_date

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, nullable=False)
    messages = db.relationship('Message', backref='conversation', lazy=True)

    def __init__(self, project_id):
        self.project_id = project_id

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('agent.id'), nullable=True)
    text = db.Column(db.String(1000), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)

    def __init__(self, conversation_id, text, user_id=None, agent_id=None, timestamp=None):
        self.conversation_id = conversation_id
        self.text = text
        self.user_id = user_id
        self.agent_id = agent_id
        self.timestamp = timestamp

class Agent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    model = db.Column(db.String(64), nullable=False)

    def __init__(self, name, model):
        self.name = name
        self.model = model

class Config(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ollama_url = db.Column(db.String(256), nullable=False)
    ollama_key = db.Column(db.String(256), nullable=False)
    model_name = db.Column(db.String(256), nullable=False)

    def __init__(self, ollama_url, ollama_key, model_name):
        self.ollama_url = ollama_url
        self.ollama_key = ollama_key
        self.model_name = model_name
