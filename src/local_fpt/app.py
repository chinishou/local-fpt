"""
Flask app for LocalFPT - Local Flow Production Tracking backend.
"""
from flask import Flask, jsonify
import os

from local_fpt.db.database import init_db, get_db_path, get_session
from local_fpt.routes.api3 import api3_bp
from local_fpt.routes.schema import schema_bp
from local_fpt.routes.info import info_bp
from local_fpt.services.schema_service import SchemaService


def create_app(db_path=None):
    app = Flask(__name__)

    if db_path:
        os.environ['FPT_DB_PATH'] = db_path

    init_db(db_path)

    SchemaService(get_session()).seed_schema()

    app.register_blueprint(api3_bp, url_prefix='/api3')
    app.register_blueprint(schema_bp, url_prefix='/schema')
    app.register_blueprint(info_bp)

    @app.route('/')
    def index():
        return jsonify({'status': 'ok', 'db': get_db_path()})

    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy'})

    return app


def run():
    """CLI entry point via `local-fpt` command."""
    app = create_app()
    app.run(host='127.0.0.1', port=8000, debug=True)


if __name__ == '__main__':
    run()
