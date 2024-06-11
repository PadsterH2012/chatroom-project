# utils.py
import git
import os

def clone_repo(repo_url, project_id):
    project_dir = os.path.join('repos', project_id)
    if not os.path.exists(project_dir):
        os.makedirs(project_dir)
    git.Repo.clone_from(repo_url, project_dir)
