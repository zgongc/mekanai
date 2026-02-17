"""
MekanAI Views Blueprint
Page rendering routes
"""
from flask import Blueprint


def create_views_blueprint():
    """Create and configure the views blueprint"""
    bp = Blueprint('views', __name__)

    # Register route modules
    from . import main
    main.register_routes(bp)

    from . import projects
    projects.register_routes(bp)

    return bp
