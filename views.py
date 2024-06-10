from app import models

def get_project_list():
    projects = models.Project.query.all()
    return jsonify([p.to_dict() for p in projects])