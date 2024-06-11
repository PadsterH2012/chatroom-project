import requests
from flask import render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Project, Agent, Config, Conversation, Message
from forms import LoginForm, RegistrationForm, ProjectForm, DeleteProjectForm, SettingsForm, AgentForm, EditGitUrlForm, CloneIngestForm
from datetime import datetime
from flask_wtf.csrf import CSRFProtect
import logging
import json
import io
from io import BytesIO
import os
import git
import subprocess

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
        clone_ingest_form = CloneIngestForm()

        if project_form.validate_on_submit() and 'create_project' in request.form:
            new_project = Project(name=project_form.name.data, git_url=project_form.git_url.data)
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
        status_class = request.args.get('status_class', 'green')
        status_message = request.args.get('status_message', 'Ingestion successful and recent')
        return render_template('chat.html', project_form=project_form, delete_project_form=delete_project_form, clone_ingest_form=clone_ingest_form, projects=projects, status_class=status_class, status_message=status_message)

    @app.route('/project/<int:project_id>', methods=['GET', 'POST'], endpoint='project_page')
    @login_required
    def project_page(project_id):
        project = Project.query.get_or_404(project_id)
        agents = Agent.query.all()
        messages = Message.query.filter_by(conversation_id=project_id).all()

        edit_git_url_form = EditGitUrlForm()
        if edit_git_url_form.validate_on_submit():
            project.git_url = edit_git_url_form.git_url.data
            db.session.commit()
            flash('Git URL updated successfully!', 'success')
            return redirect(url_for('project_page', project_id=project.id))

        project_dir = f"./repos/{project.id}"
        code_files = []
        if os.path.exists(project_dir):
            for root, dirs, files in os.walk(project_dir):
                for file in files:
                    if file.endswith('.py') or file.endswith('.txt') or file.endswith('.md'):
                        with open(os.path.join(root, file), 'r') as f:
                            code_files.append({'filename': file, 'content': f.read()})

        clone_ingest_form = CloneIngestForm()
        status_class = request.args.get('status_class', 'green')
        status_message = request.args.get('status_message', 'Ingestion successful and recent')
        return render_template('conversation.html', project=project, agents=agents, messages=messages, code_files=code_files, edit_git_url_form=edit_git_url_form, clone_ingest_form=clone_ingest_form, status_class=status_class, status_message=status_message)

    @app.route('/clone_repo/<int:project_id>', methods=['POST'])
    @login_required
    def clone_project_repo(project_id):
        project = Project.query.get_or_404(project_id)
        repo_url = project.git_url
        project_dir = f"./repos/{project.id}"

        if not repo_url:
            flash('Git URL is not set for this project.', 'error')
            return redirect(url_for('project_page', project_id=project.id))

        try:
            if os.path.exists(project_dir):
                git.Repo(project_dir).remote().pull()
            else:
                git.Repo.clone_from(repo_url, project_dir)
            flash('Repository cloned successfully!', 'success')
        except Exception as e:
            flash(f'Failed to clone repository: {str(e)}', 'error')
        return redirect(url_for('project_page', project_id=project.id))

    @app.route('/clone_and_ingest', methods=['POST'])
    @login_required
    def clone_and_ingest():
        form = CloneIngestForm()
        if form.validate_on_submit():
            project_url = form.project_url.data
            # Clone the repository
            clone_result = clone_repository(project_url)
            if clone_result:
                # Ingest the repository
                ingest_result = ingest_repository()
                if ingest_result:
                    flash('Repository cloned and ingested successfully', 'success')
                    status_class = 'green'
                    status_message = 'Ingestion successful and recent'
                else:
                    flash('Repository ingestion failed', 'error')
                    status_class = 'red'
                    status_message = 'Ingestion failed or outdated'
            else:
                flash('Repository cloning failed', 'error')
                status_class = 'red'
                status_message = 'Cloning failed or outdated'
        else:
            flash('Invalid project URL', 'error')
            status_class = 'red'
            status_message = 'Invalid project URL'
        return redirect(url_for('chat', status_class=status_class, status_message=status_message))

    @app.route('/ingest_repo/<int:project_id>', methods=['POST'])
    @login_required
    def ingest_repo(project_id):
        project = Project.query.get_or_404(project_id)
        project_dir = f"./repos/{project.id}"

        if not os.path.exists(project_dir):
            flash('Repository has not been cloned for this project.', 'error')
            return redirect(url_for('project_page', project_id=project.id))

        code_contents = []
        for root, dirs, files in os.walk(project_dir):
            for file in files:
                if file.endswith('.py') or file.endswith('.txt') or file.endswith('.md'):
                    with open(os.path.join(root, file), 'r') as f:
                        code_contents.append(f.read())

        payload = {
            'project_id': project.id,
            'code_contents': code_contents
        }

        try:
            # Simulate sending the code to the agent for ingestion
            # Replace this with the actual endpoint and payload format as required by your agent
            response = requests.post('http://your-agent-endpoint/ingest', json=payload)
            response.raise_for_status()
            flash('Repository ingested successfully!', 'success')
        except requests.RequestException as e:
            flash(f'Failed to ingest repository: {str(e)}', 'error')

        return redirect(url_for('project_page', project_id=project.id))

    def clone_repository(project_url):
        try:
            # Assuming you have a directory where repositories are stored
            repo_dir = "/path/to/repos"
            repo_name = project_url.split('/')[-1].replace('.git', '')
            repo_path = os.path.join(repo_dir, repo_name)
            
            # Remove existing directory if it exists for a fresh clone
            if os.path.exists(repo_path):
                subprocess.run(['rm', '-rf', repo_path], check=True)
            
            subprocess.run(['git', 'clone', project_url, repo_path], check=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def ingest_repository():
        # Implement your ingestion logic here
        # For example, parsing files, loading them into a database, etc.
        return True

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

        # Send the message to the appropriate API
        if agent.is_openai:
            openai_url = 'https://api.openai.com/v1/chat/completions'
            headers = {
                'Authorization': f'Bearer {config.openai_api_key}',
                'Content-Type': 'application/json'
            }
            payload = {
                'model': agent.model,
                'messages': [
                    {'role': 'system', 'content': 'You are a helpful assistant.'},
                    {'role': 'user', 'content': message_text}
                ],
                'max_tokens': 150,
                'temperature': 0.7,
                'top_p': 1.0,
                'n': 1,
                'stream': False,
                'logprobs': None,
                'stop': None
            }

            try:
                logging.info(f"Sending request to OpenAI API: {openai_url}")
                logging.info(f"Payload: {payload}")
                response = requests.post(openai_url, json=payload, headers=headers)
                logging.info(f"Response status code: {response.status_code}")
                logging.info(f"Response content: {response.content}")
                response.raise_for_status()

                openai_response = response.json()
                agent_reply = openai_response['choices'][0]['message']['content'].strip()

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
        else:
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

            # Include code files in the payload
            project = Project.query.get(project_id)
            project_dir = f"./repos/{project.id}"
            code_files = []
            if os.path.exists(project_dir):
                for root, dirs, files in os.walk(project_dir):
                    for file in files:
                        if file.endswith('.py') or file.endswith('.txt') or file.endswith('.md'):
                            with open(os.path.join(root, file), 'r') as f:
                                code_files.append({'filename': file, 'content': f.read()})

            payload['code_files'] = code_files

            try:
                logging.info(f"Sending request to Ollama API: {ollama_url}")
                logging.info(f"Payload: {payload}")
                response = requests.post(ollama_url, json=payload, headers=headers)
                logging.info(f"Response status code: {response.status_code}")
                logging.info(f"Response content: {response.content}")
                response.raise_for_status()

                # Parse the streaming JSON response
                ollama_responses = []
                for line in response.iter_lines():
                    if line:
                        ollama_response = json.loads(line.decode('utf-8'))
                        ollama_responses.append(ollama_response['response'])

                agent_reply = " ".join(ollama_responses)

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
                current_config.chatgpt_url = settings_form.chatgpt_url.data
                current_config.chatgpt_key = settings_form.chatgpt_key.data
                current_config.chatgpt_model = settings_form.chatgpt_model.data
                current_config.openai_api_key = settings_form.openai_api_key.data
                logging.info(f"Updated existing config: {current_config}")
            else:
                new_config = Config(
                    ollama_url=settings_form.ollama_url.data,
                    ollama_key=settings_form.ollama_key.data,
                    model_name=settings_form.model_name.data,
                    chatgpt_url=settings_form.chatgpt_url.data,
                    chatgpt_key=settings_form.chatgpt_key.data,
                    chatgpt_model=settings_form.chatgpt_model.data,
                    openai_api_key=settings_form.openai_api_key.data
                )
                db.session.add(new_config)
                logging.info(f"Added new config: {new_config}")
            db.session.commit()
            flash('Settings updated successfully!', 'success')
            return redirect(url_for('settings'))

        if agent_form.validate_on_submit():
            if 'create_agent' in request.form:
                new_agent = Agent(name=agent_form.name.data, model=agent_form.model.data, is_openai=agent_form.is_openai.data)
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

    @app.route('/export_settings', methods=['GET'])
    @login_required
    def export_settings():
        config = Config.query.first()
        agents = Agent.query.all()

        if not config:
            return jsonify({'error': 'No settings found to export'}), 404

        settings_data = {
            'ollama_url': config.ollama_url,
            'ollama_key': config.ollama_key,
            'model_name': config.model_name,
            'chatgpt_url': config.chatgpt_url,
            'chatgpt_key': config.chatgpt_key,
            'chatgpt_model': config.chatgpt_model,
            'openai_api_key': config.openai_api_key,
            'agents': [{'name': agent.name, 'model': agent.model, 'is_openai': agent.is_openai} for agent in agents]
        }

        settings_json = json.dumps(settings_data, indent=4)
        settings_io = BytesIO(settings_json.encode('utf-8'))
        settings_io.seek(0)

        return send_file(settings_io, as_attachment=True, download_name='settings.json', mimetype='application/json')

    @app.route('/import_settings', methods=['POST'])
    @login_required
    def import_settings():
        if 'settings_file' not in request.files:
            flash('No file part', 'error')
            return redirect(url_for('settings'))

        file = request.files['settings_file']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(url_for('settings'))

        if file:
            try:
                settings_data = json.load(file)
                config = Config.query.first()
                if not config:
                    config = Config(
                        ollama_url=settings_data['ollama_url'],
                        ollama_key=settings_data['ollama_key'],
                        model_name=settings_data['model_name'],
                        chatgpt_url=settings_data['chatgpt_url'],
                        chatgpt_key=settings_data['chatgpt_key'],
                        chatgpt_model=settings_data['chatgpt_model'],
                        openai_api_key=settings_data['openai_api_key']
                    )
                    db.session.add(config)
                else:
                    config.ollama_url = settings_data['ollama_url']
                    config.ollama_key = settings_data['ollama_key']
                    config.model_name = settings_data['model_name']
                    config.chatgpt_url = settings_data['chatgpt_url']
                    config.chatgpt_key = settings_data['chatgpt_key']
                    config.chatgpt_model = settings_data['chatgpt_model']
                    config.openai_api_key = settings_data['openai_api_key']

                # Remove existing agents
                Agent.query.delete()

                # Add new agents
                for agent_data in settings_data['agents']:
                    new_agent = Agent(name=agent_data['name'], model=agent_data['model'], is_openai=agent_data['is_openai'])
                    db.session.add(new_agent)

                db.session.commit()
                flash('Settings imported successfully!', 'success')
            except Exception as e:
                logging.error(f"Failed to import settings: {str(e)}")
                flash(f'Failed to import settings: {str(e)}', 'error')

        return redirect(url_for('settings'))
