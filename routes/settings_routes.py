from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from models import db, Config, Agent, Project, Conversation, Message
from forms import SettingsForm, AgentForm
import json
from io import BytesIO
from datetime import datetime

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    settings_form = SettingsForm()
    agent_form = AgentForm()

    current_config = Config.query.first()
    if current_config:
        settings_form = SettingsForm(obj=current_config)

    if settings_form.validate_on_submit() and 'submit' in request.form:
        if current_config:
            current_config.ollama_url = settings_form.ollama_url.data
            current_config.ollama_key = settings_form.ollama_key.data
            current_config.model_name = settings_form.model_name.data
            current_config.openai_api_key = settings_form.openai_api_key.data
        else:
            new_config = Config(
                ollama_url=settings_form.ollama_url.data,
                ollama_key=settings_form.ollama_key.data,
                model_name=settings_form.model_name.data,
                openai_api_key=settings_form.openai_api_key.data
            )
            db.session.add(new_config)
        db.session.commit()
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('settings.settings'))

    if agent_form.validate_on_submit() and 'create_agent' in request.form:
        new_agent = Agent(name=agent_form.name.data, model=agent_form.model.data, is_openai=agent_form.is_openai.data)
        db.session.add(new_agent)
        db.session.commit()
        flash('Agent created successfully!', 'success')
        return redirect(url_for('settings.settings'))

    agents = Agent.query.all()
    projects = Project.query.all()
    return render_template('settings.html', settings_form=settings_form, agent_form=agent_form, agents=agents, projects=projects)

@settings_bp.route('/remove_agent', methods=['POST'])
@login_required
def remove_agent():
    agent_id = request.form.get('agent_id')
    agent = Agent.query.get(agent_id)
    if agent:
        db.session.delete(agent)
        db.session.commit()
        flash('Agent removed successfully!', 'success')
    else:
        flash('Agent not found!', 'error')
    return redirect(url_for('settings.settings'))

@settings_bp.route('/export_settings', methods=['GET'])
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
        'openai_api_key': config.openai_api_key,
        'agents': [{'name': agent.name, 'model': agent.model, 'is_openai': agent.is_openai} for agent in agents]
    }

    settings_json = json.dumps(settings_data, indent=4)
    settings_io = BytesIO(settings_json.encode('utf-8'))
    settings_io.seek(0)

    return send_file(settings_io, as_attachment=True, download_name='settings.json', mimetype='application/json')

@settings_bp.route('/import_settings', methods=['POST'])
@login_required
def import_settings():
    if 'settings_file' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('settings.settings'))

    file = request.files['settings_file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('settings.settings'))

    if file:
        try:
            settings_data = json.load(file)
            config = Config.query.first()
            if not config:
                config = Config(
                    ollama_url=settings_data['ollama_url'],
                    ollama_key=settings_data['ollama_key'],
                    model_name=settings_data['model_name'],
                    openai_api_key=settings_data['openai_api_key']
                )
                db.session.add(config)
            else:
                config.ollama_url = settings_data['ollama_url']
                config.ollama_key = settings_data['ollama_key']
                config.model_name = settings_data['model_name']
                config.openai_api_key = settings_data['openai_api_key']

            Agent.query.delete()
            for agent_data in settings_data['agents']:
                new_agent = Agent(name=agent_data['name'], model=agent_data['model'], is_openai=agent_data['is_openai'])
                db.session.add(new_agent)

            db.session.commit()
            flash('Settings imported successfully!', 'success')
        except Exception as e:
            flash(f'Failed to import settings: {str(e)}', 'error')

    return redirect(url_for('settings.settings'))

@settings_bp.route('/export_projects', methods=['GET', 'POST'])
@login_required
def export_projects():
    if request.method == 'POST':
        project_ids = request.form.getlist('project_ids')
        if not project_ids:
            flash('No projects selected for export.', 'error')
            return redirect(url_for('settings.export_projects'))

        project_data = []
        for project_id in project_ids:
            project = Project.query.get(project_id)
            if project:
                project_info = {
                    'name': project.name,
                    'description': project.description,
                    'git_url': project.git_url,
                    'goals': project.goals,
                    'objectives': project.objectives,
                    'features': project.features,
                    'steps': project.steps,
                    'conversations': [
                        {
                            'text': message.text,
                            'timestamp': message.timestamp.isoformat(),
                            'user_id': message.user_id,
                            'agent_id': message.agent_id
                        } for message in Message.query.filter_by(conversation_id=project.id).all()
                    ]
                }
                project_data.append(project_info)

        output = BytesIO()
        filename = f"project_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output.write(json.dumps(project_data).encode('utf-8'))
        output.seek(0)

        return send_file(output, as_attachment=True, download_name=filename, mimetype='application/json')

    projects = Project.query.all()
    return render_template('export_projects.html', projects=projects)

@settings_bp.route('/import_projects', methods=['POST'])
@login_required
def import_projects():
    if 'projects_file' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('settings.settings'))

    file = request.files['projects_file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('settings.settings'))

    if file:
        try:
            projects_data = json.load(file)
            for project_data in projects_data:
                project_info = project_data['project']
                project = Project(
                    name=project_info['name'],
                    description=project_info['description'],
                    git_url=project_info['git_url'],
                    goals=project_info['goals'],
                    objectives=project_info['objectives'],
                    features=project_info['features'],
                    steps=project_info['steps']
                )
                db.session.add(project)
                db.session.commit()

                for conversation_data in project_data['conversations']:
                    conversation = Conversation(project_id=project.id)
                    db.session.add(conversation)
                    db.session.commit()

                    for message_data in conversation_data['messages']:
                        message = Message(
                            conversation_id=conversation.id,
                            text=message_data['text'],
                            timestamp=datetime.fromisoformat(message_data['timestamp']),
                            agent_id=message_data['agent_id'],
                            user_id=message_data['user_id']
                        )
                        db.session.add(message)
                        db.session.commit()

            flash('Projects imported successfully!', 'success')
        except Exception as e:
            flash(f'Failed to import projects: {str(e)}', 'error')

    return redirect(url_for('settings.settings'))
