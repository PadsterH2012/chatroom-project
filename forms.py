from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, DateField
from wtforms.validators import DataRequired, Length, Email, EqualTo, URL, Optional, ValidationError
from models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm = PasswordField('Confirm Password', validators=[
        DataRequired(), 
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

class ProjectForm(FlaskForm):
    name = StringField('Project Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    repository_url = StringField('Repository URL', validators=[Optional(), URL()])
    objective = TextAreaField('Objective', validators=[Optional()])
    key_features_components = TextAreaField('Key Features & Components', validators=[Optional()])
    implementation_strategy = TextAreaField('Implementation Strategy', validators=[Optional()])
    software_stack = TextAreaField('Software Stack', validators=[Optional()])
    start_date = DateField('Start Date', validators=[Optional()])
    end_date = DateField('End Date', validators=[Optional()])
    submit = SubmitField('Create Project')

class EditProjectForm(FlaskForm):
    name = StringField('Project Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    repository_url = StringField('Repository URL', validators=[Optional(), URL()])
    objective = TextAreaField('Objective', validators=[Optional()])
    key_features_components = TextAreaField('Key Features & Components', validators=[Optional()])
    implementation_strategy = TextAreaField('Implementation Strategy', validators=[Optional()])
    software_stack = TextAreaField('Software Stack', validators=[Optional()])
    start_date = DateField('Start Date', validators=[Optional()])
    end_date = DateField('End Date', validators=[Optional()])
    submit = SubmitField('Update Project')

class DeleteProjectForm(FlaskForm):
    id = StringField('Project ID', validators=[DataRequired()])
    submit = SubmitField('Delete Project')

class SettingsForm(FlaskForm):
    ollama_url = StringField('Ollama URL', validators=[DataRequired()])
    ollama_key = StringField('Ollama Key', validators=[DataRequired()])
    model_name = StringField('Model Name', validators=[DataRequired()])
    openai_api_key = StringField('OpenAI API Key', validators=[Optional()])
    submit = SubmitField('Save Settings')

class AgentForm(FlaskForm):
    name = StringField('Agent Name', validators=[DataRequired()])
    model = StringField('Model', validators=[DataRequired()])
    is_openai = BooleanField('Is OpenAI')
    submit = SubmitField('Create Agent')

class EditGitUrlForm(FlaskForm):
    git_url = StringField('Git URL', validators=[DataRequired(), URL()])
    submit = SubmitField('Update Git URL')

class CloneIngestForm(FlaskForm):
    project_url = StringField('Project URL', validators=[DataRequired(), URL()])
    submit = SubmitField('Clone and Ingest')
