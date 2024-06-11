from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class ProjectForm(FlaskForm):
    name = StringField('Project Name', validators=[DataRequired()])
    git_url = StringField('Git URL', validators=[DataRequired()])
    submit = SubmitField('Create Project')

class DeleteProjectForm(FlaskForm):
    id = StringField('Project ID', validators=[DataRequired()])
    submit = SubmitField('Delete Project')

class SettingsForm(FlaskForm):
    ollama_url = StringField('Ollama URL', validators=[DataRequired()])
    ollama_key = StringField('Ollama Key', validators=[DataRequired()])
    model_name = StringField('Model Name', validators=[DataRequired()])
    chatgpt_url = StringField('ChatGPT URL', validators=[DataRequired()])
    chatgpt_key = StringField('ChatGPT Key', validators=[DataRequired()])
    chatgpt_model = StringField('ChatGPT Model', validators=[DataRequired()])
    openai_api_key = StringField('OpenAI API Key', validators=[DataRequired()])
    submit = SubmitField('Update Settings')

class AgentForm(FlaskForm):
    name = StringField('Agent Name', validators=[DataRequired()])
    model = StringField('Model', validators=[DataRequired()])
    is_openai = BooleanField('Is OpenAI Agent')
    create_agent = SubmitField('Create Agent')

class EditGitUrlForm(FlaskForm):
    git_url = StringField('Git URL', validators=[DataRequired()])
    submit = SubmitField('Update Git URL')

class CloneIngestForm(FlaskForm):
    project_url = StringField('Project URL', validators=[DataRequired()])
    submit = SubmitField('Clone and Ingest')
