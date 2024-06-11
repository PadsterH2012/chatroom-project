# forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, BooleanField
from wtforms.validators import DataRequired, EqualTo, Length

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6),
        EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')
    submit = SubmitField('Register')

class ProjectForm(FlaskForm):
    name = StringField('Project Name', validators=[DataRequired(), Length(min=1, max=100)])
    git_url = StringField('Git URL', validators=[Length(max=256)])
    submit = SubmitField('Create Project')

class DeleteProjectForm(FlaskForm):
    id = IntegerField('Project ID', validators=[DataRequired()])
    submit = SubmitField('Delete Project')

class SettingsForm(FlaskForm):
    ollama_url = StringField('Ollama URL', validators=[DataRequired(), Length(max=256)])
    ollama_key = StringField('Ollama API Key', validators=[DataRequired(), Length(max=256)])
    model_name = StringField('Model Name', validators=[DataRequired(), Length(max=256)])
    chatgpt_url = StringField('ChatGPT URL', validators=[Length(max=256)])
    chatgpt_key = StringField('ChatGPT API Key', validators=[Length(max=256)])
    chatgpt_model = StringField('ChatGPT Model', validators=[Length(max=256)])
    openai_api_key = StringField('OpenAI API Key', validators=[Length(max=256)])  # Add this line
    submit = SubmitField('Save Settings')

class AgentForm(FlaskForm):
    name = StringField('Agent Name', validators=[DataRequired(), Length(min=1, max=64)])
    model = StringField('Model', validators=[DataRequired(), Length(min=1, max=64)])
    is_openai = BooleanField('Is OpenAI')  # Add this line
    create_agent = SubmitField('Create Agent')
    remove_agent = SubmitField('Remove Agent')

class EditGitUrlForm(FlaskForm):
    git_url = StringField('Git URL', validators=[DataRequired(), Length(max=256)])
    submit = SubmitField('Save')
