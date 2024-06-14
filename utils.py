import os
import subprocess
import shutil

def clone_repo(project_url, project_id):
    repo_dir = f"./repos/{project_id}"
    if os.path.exists(repo_dir):
        shutil.rmtree(repo_dir)
    try:
        subprocess.run(['git', 'clone', project_url, repo_dir], check=True)
    except subprocess.CalledProcessError as e:
        raise Exception(f"Cmd('git') failed due to: {str(e)}")

def read_project_files(project_id):
    project_dir = f"./repos/{project_id}"
    code_contents = []
    for root, dirs, files in os.walk(project_dir):
        for file in files:
            if file.endswith(('.py', '.js', '.css', '.html', '.txt', '.md')):
                with open(os.path.join(root, file), 'r') as f:
                    code_contents.append({'filename': file, 'content': f.read()})
    return code_contents

def remove_repo(project_id):
    repo_dir = f"./repos/{project_id}"
    if os.path.exists(repo_dir):
        shutil.rmtree(repo_dir)
