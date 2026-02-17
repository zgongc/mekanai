"""
MekanAI - AI Interior Design Application
========================================

Modular architecture:
    - Config: config.py + config.yaml
    - Views:  views/ (page routes)
    - API:    api/   (REST endpoints)
"""
from flask import Flask, session
from dotenv import load_dotenv
from config import Config

# .env dosyasından API key'leri yükle (DB'de yoksa env'den okunur)
load_dotenv('configs/.env')

# Import blueprints
from views import create_views_blueprint
from api import create_api_blueprint
from models.base import init_db, shutdown_session


def create_app():
    """Application factory"""

    # Load configuration
    config = Config()
    config.validate()
    config.ensure_directories()

    # Initialize database tables
    init_db()

    # Create Flask app
    app = Flask(__name__)
    app.secret_key = config.get('server.secret_key', 'mekanai-change-this')
    app.config['MAX_CONTENT_LENGTH'] = config.get('server.max_upload_size', 16777216)
    app.config['APP_CONFIG'] = config

    # Register session cleanup
    app.teardown_appcontext(shutdown_session)

    # Register blueprints
    app.register_blueprint(create_views_blueprint())
    app.register_blueprint(create_api_blueprint())

    # Theme context processor
    @app.context_processor
    def inject_globals():
        return {
            'theme': session.get('theme', config.get('system.theme', 'dark')),
            'app_name': config.get('system.name', 'MekanAI'),
            'app_version': config.get('system.version', '1.0.0')
        }

    # Error handlers
    register_error_handlers(app)

    @app.after_request
    def add_headers(response):
        # Keep-alive for long-running AI generation requests
        response.headers['Connection'] = 'keep-alive'
        response.headers['Keep-Alive'] = 'timeout=300'
        # Cache static files (CSS, JS, images, fonts)
        if response.content_type and any(t in response.content_type for t in
                ('text/css', 'javascript', 'image/', 'font/')):
            response.headers['Cache-Control'] = 'public, max-age=3600'
        return response

    print(f"[+] {config.get('system.name')} v{config.get('system.version')} initialized")

    return app


def register_error_handlers(app):
    """Register error handlers"""
    from flask import render_template

    @app.errorhandler(404)
    def not_found(error):
        return render_template('error.html',
                             error_code=404,
                             error_message='Sayfa bulunamadı'), 404

    @app.errorhandler(500)
    def server_error(error):
        return render_template('error.html',
                             error_code=500,
                             error_message='Sunucu hatası'), 500


# Create app instance
app = create_app()

if __name__ == '__main__':
    config = app.config['APP_CONFIG']

    app.run(
        host=config.get('server.host', '0.0.0.0'),
        port=config.get('server.port', 5000),
        debug=config.get('system.debug_mode', True),
        threaded=True
    )
