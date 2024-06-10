import requests
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Project, Agent, Config, Conversation, Message
from forms import LoginForm, RegistrationForm, ProjectForm, DeleteProjectForm, SettingsForm, AgentForm
from datetime import datetime
from flask_wtf.csrf import CSRFProtect
import logging

csrf = CSRFProtect()

def init_routes(app):
    csrf.init_app(app)
    
    logging.basicConfig(level=logging.INFO)
    
    @app.route('/')
    def home():
        return render_template('index.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('chat'))
        form = LoginForm()
        if form.validate_on_submit():
            username = form.username.data
            password = form.password.data
            user = User.query.filter_by(username=username).first()
            if user and check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for('chat'))
            else:
                flash('Invalid username or password', 'error')
        return render_template('login.html', title='Login', form=form)

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('chat'))
        form = RegistrationForm()
        if form.validate_on_submit():
            hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
            new_user = User(username=form.username.data, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('login'))
        return render_template('register.html', title='Register', form=form)

    @app.route('/logout', methods=['GET'])
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))

    @app.route('/chat', methods=['GET', 'POST'])
    @login_required
    def chat():
        project_form = ProjectForm()
        delete_project_form = DeleteProjectForm()

        if project_form.validate_on_submit() and 'create_project' in request.form:
            new_project = Project(name=project_form.name.data)
            db.session.add(new_project)
            db.session.commit()
            flash('Project created successfully!', 'success')
            return redirect(url_for('chat'))

        if delete_project_form.validate_on_submit() and request.form.get('form_type') == 'delete_project':
            project_id = delete_project_form.id.data
            project = db.session.get(Project, project_id)
            if project:
                db.session.delete(project)
                db.session.commit()
                flash('Project deleted successfully!', 'success')
            else:
                flash('Project not found!', 'error')
            return redirect(url_for('chat'))

        projects = Project.query.all()
        return render_template('chat.html', project_form=project_form, delete_project_form=delete_project_form, projects=projects)

    @app.route('/project/<int:project_id>', methods=['GET', 'POST'], endpoint='project_page')
    @login_required
    def project_page(project_id):
        project = Project.query.get_or_404(project_id)
        agents = Agent.query.all()
        messages = Message.query.filter_by(conversation_id=project_id).all()
        return render_template('conversation.html', project=project, agents=agents, messages=messages)

    @app.route('/send_message', methods=['POST'], endpoint='send_message')
    @login_required
    def send_message():
        data = request.json
        project_id = data.get('project_id')
        agent_id = data.get('agent_id')
        message_text = data.get('message')

        if not project_id or not agent_id or not message_text:
            logging.error('Invalid request data')
            return jsonify({'error': 'Invalid request data'}), 400

        # Save user message to the database
        conversation = Conversation.query.filter_by(project_id=project_id).first()
        if not conversation:
            conversation = Conversation(project_id=project_id)
            db.session.add(conversation)
            db.session.commit()

        user_message = Message(conversation_id=conversation.id, user_id=current_user.id, agent_id=None, text=message_text, timestamp=datetime.utcnow())
        db.session.add(user_message)
        db.session.commit()

        # Get the agent and its associated Ollama URL from the database
        agent = Agent.query.get(agent_id)
        config = Config.query.first()

        if not agent:
            logging.error('Agent not found')
            return jsonify({'error': 'Agent not found'}), 404

        if not config:
            logging.error('Configuration not found')
            return jsonify({'error': 'Configuration not found'}), 404

        # Send the message to the Ollama API
        ollama_url = config.ollama_url
        ollama_key = config.ollama_key
        model_name = agent.model

        headers = {
            'Authorization': f'Bearer {ollama_key}',
            'Content-Type': 'application/json'
        }
        payload = {
            'model': model_name,
            'prompt': message_text
        }

        try:
            response = requests.post(ollama_url, json=payload, headers=headers)
            response.raise_for_status()
            ollama_response = response.json()
            agent_reply = ollama_response.get('response', 'No reply from agent')

            # Save agent's reply to the database
            agent_message = Message(
                conversation_id=conversation.id,
                user_id=None,
                agent_id=agent.id,
                text=agent_reply,
                timestamp=datetime.utcnow()
            )
            db.session.add(agent_message)
            db.session.commit()

            return jsonify({'reply': agent_reply})

        except requests.RequestException as e:
            logging.error(f'Failed to communicate with agent: {str(e)}')
            return jsonify({'error': f'Failed to communicate with agent: {str(e)}'}), 500

    @app.route('/settings', methods=['GET', 'POST'], endpoint='settings')
@login_required
def settings():
    settings_form = SettingsForm()
    agent_form = AgentForm()

    current_config = Config.query.first()
    if current_config:
        settings_form = SettingsForm(obj=current_config)

    if settings_form.validate_on_submit() and 'submit' in request.form:
        logging.info("Settings form submitted")
        if current_config:
            current_config.ollama_url = settings_form.ollama_url.data
            current_config.ollama_key = settings_form.ollama_key.data
            current_config.model_name = settings_form.model_name.data
            logging.info(f"Updated existing config: {current_config}")
        else:
            new_config = Config(
                ollama_url=settings_form.ollama_url.data,
                ollama_key=settings_form.ollama_key.data,
                model_name=settings_form.model_name.data
            )
            db.session.add(new_config)
            logging.info(f"Added new config: {new_config}")
        db.session.commit()
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('settings'))

    if agent_form.validate_on_submit():
        if 'create_agent' in request.form:
            new_agent = Agent(name=agent_form.name.data, model=agent_form.model.data)
            db.session.add(new_agent)
            db.session.commit()
            flash('Agent created successfully!', 'success')
        return redirect(url_for('settings'))

    if request.method == 'POST' and 'remove_agent' in request.form:
        agent_id = request.form.get('agent_id')
        print(f"Attempting to remove agent with ID: {agent_id}")
        agent = Agent.query.get(agent_id)
        if agent:
            print(f"Found agent: {agent.name}")
            db.session.delete(agent)
            db.session.commit()
            flash('Agent removed successfully!', 'success')
        else:
            print("Agent not found")
            flash('Agent not found!', 'error')
        return redirect(url_for('settings'))

    agents = Agent.query.all()
    return render_template('settings.html', settings_form=settings_form, agent_form=agent_form, agents=agents)
