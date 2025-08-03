from flask import Flask, request, jsonify
from app import process_document, process_query
import json
import os
import tempfile

app = Flask(__name__, static_folder='static')

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'document' not in request.files:
        return jsonify({"error": "No document provided"}), 400
    
    file = request.files['document']
    metadata_str = request.form.get('metadata', '{}')
    
    try:
        metadata = json.loads(metadata_str)
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid metadata JSON"}), 400
    
    # Save file temporarily
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    file.save(temp_file.name)
    temp_file.close()
    
    try:
        chunks_processed = process_document(temp_file.name, metadata)
        os.unlink(temp_file.name)  # Delete temp file
        return jsonify({"success": True, "chunks_processed": chunks_processed})
    except Exception as e:
        os.unlink(temp_file.name)  # Delete temp file
        return jsonify({"error": str(e)}), 500

@app.route('/query', methods=['POST'])
def query():
    data = request.json
    if not data or 'query' not in data:
        return jsonify({"error": "No query provided"}), 400
    
    try:
        result = process_query(data['query'])
        # Parse result or format as needed
        response = {
            "decision": result,
            # Add other fields as needed based on your original implementation
        }
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)