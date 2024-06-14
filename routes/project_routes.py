# project_routes.py

import os
import subprocess
import logging
import json
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required
from models import db, Project, Agent, Message, Conversation
from forms import ProjectForm, EditProjectForm, DeleteProjectForm, CloneIngestForm, EditGitUrlForm
from socketio_instance import socketio

project_bp = Blueprint('project', __name__)

@project_bp.route('/project_room', methods=['GET', 'POST'])
@login_required
def project_room():
    project_form = ProjectForm()
    delete_project_form = DeleteProjectForm()
    clone_ingest_form = CloneIngestForm()

    if project_form.validate_on_submit() and 'create_project' in request.form:
        new_project = Project(name=project_form.name.data, repository_url=project_form.repository_url.data)
        db.session.add(new_project)
        db.session.commit()
        flash('Project created successfully!', 'success')
        return redirect(url_for('project.project_room'))

    if delete_project_form.validate_on_submit() and request.form.get('form_type') == 'delete_project':
        project_id = delete_project_form.id.data
        project = Project.query.get(project_id)
        if project:
            db.session.delete(project)
            db.session.commit()
            flash('Project deleted successfully!', 'success')
        else:
            flash('Project not found!', 'error')
        return redirect(url_for('project.project_room'))

    projects = Project.query.all()
    status_class = request.args.get('status_class', 'green')
    status_message = request.args.get('status_message', 'Ingestion successful and recent')
    return render_template('project_room.html', project_form=project_form, delete_project_form=delete_project_form, clone_ingest_form=clone_ingest_form, projects=projects, status_class=status_class, status_message=status_message)

@project_bp.route('/project/<int:project_id>', methods=['GET', 'POST'])
@login_required
def project_page(project_id):
    project = Project.query.get_or_404(project_id)
    agents = Agent.query.all()
    messages = Message.query.filter_by(conversation_id=project_id).all()

    agents_dict = {agent.id: agent for agent in agents}

    edit_git_url_form = EditGitUrlForm()
    if edit_git_url_form.validate_on_submit():
        project.repository_url = edit_git_url_form.repository_url.data
        db.session.commit()
        flash('Git URL updated successfully!', 'success')
        return redirect(url_for('project.project_page', project_id=project.id))

    project_dir = f"./repos/{project.id}"
    code_files = []
    if os.path.exists(project_dir):
        for root, dirs, files in os.walk(project_dir):
            for file in files:
                if file.endswith(('.py', '.txt', '.md', '.html', '.css', '.js')):
                    with open(os.path.join(root, file), 'r') as f:
                        code_files.append({'filename': os.path.relpath(os.path.join(root, file), project_dir), 'content': f.read()})

    clone_ingest_form = CloneIngestForm()
    status_class = request.args.get('status_class', 'green')
    status_message = request.args.get('status_message', 'Ingestion successful and recent')
    return render_template('conversation.html', project=project, agents=agents, messages=messages, code_files=code_files, edit_git_url_form=edit_git_url_form, clone_ingest_form=clone_ingest_form, status_class=status_class, status_message=status_message, agents_dict=agents_dict)

@project_bp.route('/project/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    form = EditProjectForm(obj=project)

    if form.validate_on_submit():
        project.name = form.name.data
        project.description = form.description.data
        project.repository_url = form.repository_url.data
        project.objective = form.objective.data
        project.key_features_components = form.key_features_components.data
        project.implementation_strategy = form.implementation_strategy.data
        project.software_stack = form.software_stack.data
        db.session.commit()
        flash('Project updated successfully!', 'success')
        return redirect(url_for('project.project_page', project_id=project.id))

    return render_template('edit_project.html', form=form, project=project)

@project_bp.route('/clone_and_ingest/<int:project_id>', methods=['POST'])
@login_required
def clone_and_ingest(project_id):
    project = Project.query.get_or_404(project_id)
    project_url = project.repository_url

    if project_url:
        try:
            socketio.emit('progress', {'status': 'Downloading from repository...'}, namespace='/progress')
            clone_repository(project_url, project_id)
            socketio.emit('progress', {'status': 'Reading project files...'}, namespace='/progress')
            code_contents = read_project_files(project_id)
            project.ingested_code = json.dumps(code_contents)
            db.session.commit()
            socketio.emit('progress', {'status': 'Adding to database...'}, namespace='/progress')
            remove_repo(project_id)
            socketio.emit('progress', {'status': 'Removing temporary files...'}, namespace='/progress')
            flash('Repository cloned and ingested successfully', 'success')
        except Exception as e:
            socketio.emit('progress', {'status': f'Error: {str(e)}'}, namespace='/progress')
            flash(f'Error during cloning and ingestion: {str(e)}', 'error')
    else:
        flash('Repository URL not provided', 'error')

    return jsonify({'status': 'Ingestion completed'}), 200

@project_bp.route('/project_summary/<int:project_id>', methods=['GET'])
@login_required
def project_summary(project_id):
    project = Project.query.get_or_404(project_id)
    summary = {
        'name': project.name,
        'description': project.description,
        'repository_url': project.repository_url,
        'objective': project.objective,
        'key_features_components': project.key_features_components,
        'implementation_strategy': project.implementation_strategy,
        'software_stack': project.software_stack
    }
    logging.info(f'Project summary: {summary}')
    return jsonify(summary), 200

@project_bp.route('/project_ingest_summary/<int:project_id>', methods=['GET'])
@login_required
def project_ingest_summary(project_id):
    project = Project.query.get_or_404(project_id)
    try:
        code_contents = json.loads(project.ingested_code)
        file_summaries = [{'filename': file['filename'], 'lines': len(file['content'].splitlines())} for file in code_contents]
        logging.info(f'Project ingest summary: {file_summaries}')
        return jsonify(file_summaries), 200
    except json.JSONDecodeError as e:
        logging.error(f'Error decoding JSON: {str(e)}')
        return jsonify({'error': f'Error decoding JSON: {str(e)}'}), 500

def clone_repository(project_url, project_id):
    try:
        repo_dir = f"./repos/{project_id}"
        if os.path.exists(repo_dir):
            logging.info(f"Removing existing directory {repo_dir}")
            subprocess.run(['rm', '-rf', repo_dir], check=True)
        logging.info(f"Cloning repository to {repo_dir}")
        subprocess.run(['git', 'clone', project_url, repo_dir], check=True)
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Cloning failed: {str(e)}")
        return False

def read_project_files(project_id):
    project_dir = f"./repos/{project_id}"
    code_contents = []
    for root, dirs, files in os.walk(project_dir):
        for file in files:
            if file.endswith(('.py', '.txt', '.md', '.html', '.css', '.js')):
                with open(os.path.join(root, file), 'r') as f:
                    code_contents.append({'filename': os.path.relpath(os.path.join(root, file), project_dir), 'content': f.read()})
    return code_contents

def remove_repo(project_id):
    repo_dir = f"./repos/{project_id}"
    if os.path.exists(repo_dir):
        subprocess.run(['rm', '-rf', repo_dir], check=True)

@project_bp.route('/create_folder_structure/<int:project_id>', methods=['POST'])
@login_required
def create_folder_structure(project_id):
    data = request.json
    base_path = data.get('base_path', '/workspace')
    structure = data.get('structure')

    if not structure:
        return jsonify({'error': 'No structure provided'}), 400

    project_path = os.path.join(base_path, f'project_{project_id}')

    try:
        for folder, files in structure.items():
            folder_path = os.path.join(project_path, folder)
            os.makedirs(folder_path, exist_ok=True)
            for file in files:
                file_path = os.path.join(folder_path, file)
                open(file_path, 'a').close()  # Create an empty file
        return jsonify({'status': 'Folder structure created successfully'}), 200
    except Exception as e:
        logging.error(f'Error creating folder structure: {str(e)}')
        return jsonify({'error': f'Error creating folder structure: {str(e)}'}), 500
