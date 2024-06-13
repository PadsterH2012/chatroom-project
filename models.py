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
    features = db.Column(db.Text, nullable=True)
    steps = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    git_url = db.Column(db.String(256), nullable=True)
    ingested_code = db.Column(db.Text, nullable=True)

    def __init__(self, name, description=None, objectives=None, goals=None, features=None, steps=None, start_date=None, end_date=None, git_url=None, ingested_code=None):
        self.name = name
        self.description = description
        self.objectives = objectives
        self.goals = goals
        self.features = features
        self.steps = steps
        self.start_date = start_date
        self.end_date = end_date
        self.git_url = git_url
        self.ingested_code = ingested_code

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, nullable=False)
    messages = db.relationship('Message', backref='conversation', lazy=True)
    context = db.Column(db.Text, nullable=True)

    def __init__(self, project_id, context=None):
        self.project_id = project_id
        self.context = context

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
    is_openai = db.Column(db.Boolean, default=False)
    avatar = db.Column(db.String(256), nullable=True)
    color = db.Column(db.String(7), default="#3498db")

    def __init__(self, name, model, is_openai=False, avatar=None, color="#3498db"):
        self.name = name
        self.model = model
        self.is_openai = is_openai
        self.avatar = avatar
        self.color = color

    def to_dict(self):
        return {
            'name': self.name,
            'model': self.model,
            'is_openai': self.is_openai,
            'avatar': self.avatar,
            'color': self.color
        }

    @staticmethod
    def from_dict(data):
        return Agent(
            name=data['name'],
            model=data['model'],
            is_openai=data.get('is_openai', False),
            avatar=data.get('avatar'),
            color=data.get('color', "#3498db")
        )

    @property
    def initials(self):
        return ''.join([word[0] for word in self.name.split()]).upper()

class Config(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ollama_url = db.Column(db.String(256), nullable=False)
    ollama_key = db.Column(db.String(256), nullable=False)
    model_name = db.Column(db.String(256), nullable=False)
    chatgpt_url = db.Column(db.String(256), nullable=True)
    chatgpt_key = db.Column(db.String(256), nullable=True)
    chatgpt_model = db.Column(db.String(256), nullable=True)
    openai_api_key = db.Column(db.String(256), nullable=True)

    def __init__(self, ollama_url, ollama_key, model_name, chatgpt_url=None, chatgpt_key=None, chatgpt_model=None, openai_api_key=None):
        self.ollama_url = ollama_url
        self.ollama_key = ollama_key
        self.model_name = model_name
        self.chatgpt_url = chatgpt_url
        self.chatgpt_key = chatgpt_key
        self.chatgpt_model = chatgpt_model
        self.openai_api_key = openai_api_key

    def to_dict(self):
        return {
            'ollama_url': self.ollama_url,
            'ollama_key': self.ollama_key,
            'model_name': self.model_name,
            'chatgpt_url': self.chatgpt_url,
            'chatgpt_key': self.chatgpt_key,
            'chatgpt_model': self.chatgpt_model,
            'openai_api_key': self.openai_api_key
        }

    @staticmethod
    def from_dict(data):
        return Config(
            ollama_url=data['ollama_url'],
            ollama_key=data['ollama_key'],
            model_name=data['model_name'],
            chatgpt_url=data.get('chatgpt_url'),
            chatgpt_key=data.get('chatgpt_key'),
            chatgpt_model=data.get('chatgpt_model'),
            openai_api_key=data.get('openai_api_key')
        )
