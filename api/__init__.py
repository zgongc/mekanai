"""
MekanAI API Blueprint
RESTful API endpoints
"""
from flask import Blueprint


def create_api_blueprint():
    """Create and configure the API blueprint"""
    bp = Blueprint('api', __name__, url_prefix='/api')

    # Register API route modules
    from . import generate, settings
    generate.register_routes(bp)
    settings.register_routes(bp)

    return bp
