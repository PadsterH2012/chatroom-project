import requests
from flask import Blueprint, request, jsonify, current_app, render_template
from flask_login import login_required, current_user
from models import db, Project, Conversation, Message, Agent, Config
from datetime import datetime
import logging
import json

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/project/<int:project_id>', methods=['GET'])
@login_required
def conversation(project_id):
    project = Project.query.get_or_404(project_id)
    messages = Message.query.filter_by(conversation_id=project_id).order_by(Message.timestamp).all()
    agents = Agent.query.all()
    
    # Create a dictionary of agents for easy access in the template
    agents_dict = {agent.id: agent for agent in agents}

    return render_template('conversation.html', project=project, messages=messages, agents=agents, agents_dict=agents_dict)

@chat_bp.route('/send_message', methods=['POST'])
@login_required
def send_message():
    data = request.json
    project_id = data.get('project_id')
    agent_id = data.get('agent_id')
    message_text = data.get('message')

    if not project_id or not agent_id or not message_text:
        logging.error('Invalid request data')
        return jsonify({'error': 'Invalid request data'}), 400

    # Fetch project details
    project = Project.query.get(project_id)
    if not project:
        logging.error('Project not found')
        return jsonify({'error': 'Project not found'}), 404

    # Check if the message is "Tell me about the project"
    if message_text.lower() == "tell me about the project":
        project_details = f"""
        Project Name: {project.name}
        Description: {project.description or "No description available"}
        Goals: {project.goals or "No goals specified"}
        Objectives: {project.objectives or "No objectives specified"}
        Features: {project.features or "No features listed"}
        Steps: {project.steps or "No steps provided"}
        """
        message_text += f"\n\n{project_details}"

    # Save user message to the database
    conversation = Conversation.query.filter_by(project_id=project_id).first()
    if not conversation:
        conversation = Conversation(project_id=project_id)
        db.session.add(conversation)
        db.session.commit()

    user_message = Message(conversation_id=conversation.id, user_id=current_user.id, agent_id=None, text=message_text, timestamp=datetime.utcnow())
    db.session.add(user_message)
    db.session.commit()

    # Get the agent and its associated URL from the database
    agent = Agent.query.get(agent_id)
    config = Config.query.first()

    if not agent:
        logging.error('Agent not found')
        return jsonify({'error': 'Agent not found'}), 404

    if not config:
        logging.error('Configuration not found')
        return jsonify({'error': 'Configuration not found'}), 404

    # Prepare payload for the agent
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
            response = requests.post(openai_url, json=payload, headers=headers)
            response.raise_for_status()
            logging.info(f"OpenAI API response: {response.content}")
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

            return jsonify({'reply': agent_reply, 'agent_name': agent.name})

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
            'prompt': message_text,
            'context': []  # Add any additional context if needed
        }

        try:
            response = requests.post(ollama_url, json=payload, headers=headers, stream=True)
            response.raise_for_status()
            logging.info(f"Ollama API response: {response.content}")

            agent_reply = ""

            # Parse streaming response
            for line in response.iter_lines():
                if line:
                    json_line = json.loads(line.decode('utf-8'))
                    if 'response' in json_line:
                        agent_reply += json_line['response']
                    if json_line.get('done'):
                        break

            # Save agent's reply to the database
            agent_message = Message(
                conversation_id=conversation.id,
                user_id=None,
                agent_id=agent.id,
                text=agent_reply.strip(),
                timestamp=datetime.utcnow()
            )
            db.session.add(agent_message)
            db.session.commit()

            return jsonify({'reply': agent_reply.strip(), 'agent_name': agent.name})

        except requests.RequestException as e:
            logging.error(f'Failed to communicate with agent: {str(e)}')
            return jsonify({'error': f'Failed to communicate with agent: {str(e)}'}), 500
