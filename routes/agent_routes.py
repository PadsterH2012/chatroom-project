from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from extensions import db
from models import Agent
from forms import AgentForm

agent_bp = Blueprint('agent', __name__)

@agent_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    agent_form = AgentForm()
    agents = Agent.query.all()
    
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
    
    return render_template('settings.html', agent_form=agent_form, agents=agents)
