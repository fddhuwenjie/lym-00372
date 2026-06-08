from flask import Blueprint, request, jsonify
from app.services.metadata_service import MetadataService
from app.services.query_executor import QueryExecutor

api_bp = Blueprint('api', __name__)

@api_bp.route('/metadata', methods=['GET'])
def get_metadata():
    try:
        metadata = MetadataService.get_all_metadata()
        return jsonify(metadata)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/generate-sql', methods=['POST'])
def generate_sql():
    try:
        query_structure = request.get_json()
        result = QueryExecutor.generate_sql(query_structure)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@api_bp.route('/execute-query', methods=['POST'])
def execute_query():
    try:
        query_structure = request.get_json()
        result = QueryExecutor.execute(query_structure)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400
