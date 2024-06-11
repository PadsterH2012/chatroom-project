from flask import Flask, request, jsonify
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

ingested_data = {}

@app.route('/ingest', methods=['POST'])
def ingest():
    try:
        data = request.json
        project_id = data.get('project_id')
        code_contents = data.get('code_contents')

        if not project_id or not code_contents:
            return jsonify({'error': 'Invalid data'}), 400

        # Store ingested data
        ingested_data[project_id] = code_contents

        logging.info(f"Received ingestion request for project {project_id}")
        logging.info(f"Number of files received: {len(code_contents)}")

        return jsonify({'message': 'Ingestion successful'}), 200

    except Exception as e:
        logging.error(f"Ingestion failed: {str(e)}")
        return jsonify({'error': 'Ingestion failed'}), 500

@app.route('/query', methods=['POST'])
def query():
    try:
        data = request.json
        project_id = data.get('project_id')
        query_text = data.get('query')

        if not project_id or not query_text:
            return jsonify({'error': 'Invalid data'}), 400

        if project_id not in ingested_data:
            return jsonify({'error': 'Project data not found'}), 404

        # Here you would implement the logic to query the ingested data
        # For this example, we'll just return a placeholder response
        response = f"Querying the code for project {project_id}: {query_text}"
        
        logging.info(f"Received query for project {project_id}: {query_text}")
        return jsonify({'response': response}), 200

    except Exception as e:
        logging.error(f"Query failed: {str(e)}")
        return jsonify({'error': 'Query failed'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
