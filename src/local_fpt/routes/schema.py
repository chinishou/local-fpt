"""
Schema routes for LocalFPT.
"""
from flask import Blueprint, jsonify

from local_fpt.db.database import get_session
from local_fpt.services.schema_service import SchemaService


schema_bp = Blueprint('schema', __name__)


@schema_bp.route('/read', methods=['GET'])
def schema_read():
    svc = SchemaService(get_session())
    return jsonify(svc.get_schema())
