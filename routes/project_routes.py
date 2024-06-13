from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required
from forms import ProjectForm, EditProjectForm, DeleteProjectForm, CloneIngestForm, EditGitUrlForm
from models import db, Project, Agent, Message, Conversation
import os
import subprocess
import logging
import json

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
                if file.endswith('.py') or file.endswith('.txt') or file.endswith('.md'):
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
    form = CloneIngestForm()
    if form.validate_on_submit():
        project_url = form.project_url.data
        project = Project.query.get_or_404(project_id)
        project.repository_url = project_url
        db.session.commit()

        logging.info(f"Cloning repository from {project_url}")
        clone_result = clone_repository(project_url, project_id)
        if clone_result:
            logging.info("Repository cloned successfully. Starting ingestion.")
            ingest_result = ingest_repository(project_id)
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
    return redirect(url_for('project.project_page', project_id=project_id, status_class=status_class, status_message=status_message))

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

def ingest_repository(project_id):
    project_dir = f"./repos/{project_id}"
    if not os.path.exists(project_dir):
        logging.error(f"Repository directory {project_dir} does not exist")
        return False

    code_contents = []
    for root, dirs, files in os.walk(project_dir):
        for file in files:
            if file.endswith('.py') or file.endswith('.txt') or file.endswith('.md'):
                with open(os.path.join(root, file), 'r') as f:
                    code_contents.append(f.read())

    # Save ingested code to the database
    project = Project.query.get_or_404(project_id)
    project.ingested_code = json.dumps(code_contents)
    db.session.commit()

    return True
