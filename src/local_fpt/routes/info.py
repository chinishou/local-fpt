"""
Info routes for LocalFPT.
"""
from flask import Blueprint, jsonify


info_bp = Blueprint('info', __name__)


@info_bp.route('/api2', methods=['GET'])
def info_api2():
    return jsonify({
        'user_authentication_method': 'api_session',
        'version': [2024, 1, 0],
    })


@info_bp.route('/api3', methods=['GET'])
def info_api3():
    return jsonify({
        'user_authentication_method': 'api_session',
        'version': [2024, 1, 0],
    })
