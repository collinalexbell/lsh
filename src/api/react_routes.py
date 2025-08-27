"""Routes for serving React app"""
import os
from flask import Blueprint, send_from_directory, send_file

react_bp = Blueprint('react', __name__)

# Path to React build directory
REACT_BUILD_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'static', 'react-build')

@react_bp.route('/')
@react_bp.route('/robot')  # React route
def serve_react():
    """Serve React app"""
    return send_file(os.path.join(REACT_BUILD_PATH, 'index.html'))

@react_bp.route('/assets/<path:filename>')
def serve_react_assets(filename):
    """Serve React static assets"""
    return send_from_directory(os.path.join(REACT_BUILD_PATH, 'assets'), filename)