from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify  # Add jsonify here
from flask_login import login_required
from forms import ProjectForm, EditProjectForm, DeleteProjectForm, CloneIngestForm, EditGitUrlForm
from models import db, Project, Agent, Message, Conversation
import os
import subprocess
import logging
import json
from utils import clone_repo, read_project_files, remove_repo
from socketio_instance import socketio

project_bp = Blueprint('project', __name__)

# Define routes here
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
                if file.endswith(('.py', '.js', '.css', '.html', '.txt', '.md')):
                    with open(os.path.join(root, file), 'r') as f:
                        code_files.append({'filename': file, 'content': f.read()})

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
            # Step 1: Cloning the repository
            socketio.emit('progress', {'status': 'Downloading from repository...'}, namespace='/progress')
            clone_repo(project_url, project_id)

            # Step 2: Reading project files
            socketio.emit('progress', {'status': 'Reading project files...'}, namespace='/progress')
            code_contents = read_project_files(project_id)

            # Step 3: Saving to the database
            socketio.emit('progress', {'status': 'Adding to database...'}, namespace='/progress')
            project.ingested_code = json.dumps(code_contents)
            db.session.commit()

            # Step 4: Removing the repository folder
            socketio.emit('progress', {'status': 'Removing temporary files...'}, namespace='/progress')
            remove_repo(project_id)
            socketio.emit('progress', {'status': 'Repository cloned and ingested successfully'}, namespace='/progress')
            flash('Repository cloned and ingested successfully', 'success')
            return jsonify({'success': True})
        except Exception as e:
            socketio.emit('progress', {'status': f'Error: {str(e)}'}, namespace='/progress')
            flash(f'Error during cloning and ingestion: {str(e)}', 'error')
            return jsonify({'success': False, 'error': str(e)})
    else:
        socketio.emit('progress', {'status': 'Repository URL not provided'}, namespace='/progress')
        flash('Repository URL not provided', 'error')
        return jsonify({'success': False, 'error': 'Repository URL not provided'})
