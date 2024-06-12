from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from models import db, Config, Agent, Project
from forms import SettingsForm, AgentForm
import json
from io import BytesIO

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

    if agent_form.validate_on_submit():
        if 'create_agent' in request.form:
            new_agent = Agent(name=agent_form.name.data, model=agent_form.model.data, is_openai=agent_form.is_openai.data)
            db.session.add(new_agent)
            db.session.commit()
            flash('Agent created successfully!', 'success')
        elif 'remove_agent' in request.form:
            agent_id = request.form.get('agent_id')
            agent = Agent.query.get(agent_id)
            if agent:
                db.session.delete(agent)
                db.session.commit()
                flash('Agent removed successfully!', 'success')
            else:
                flash('Agent not found!', 'error')
        return redirect(url_for('settings.settings'))

    agents = Agent.query.all()
    projects = Project.query.all()
    return render_template('settings.html', settings_form=settings_form, agent_form=agent_form, agents=agents, projects=projects)

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
