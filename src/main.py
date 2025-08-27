"""Main Flask application entry point"""
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

from .api.robot_routes import robot_bp
from .api.camera_routes import camera_bp
from .api.position_routes import position_bp
from .api.react_routes import react_bp
from .services.robot_controller import robot_controller
from .services.position_service import position_service
from .utils.config import SECRET_KEY, CORS_ALLOWED_ORIGINS, HOST, PORT, DEBUG

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    
    app.config['SECRET_KEY'] = SECRET_KEY
    
    # Initialize SocketIO
    socketio = SocketIO(app, cors_allowed_origins=CORS_ALLOWED_ORIGINS)
    
    # Register blueprints
    app.register_blueprint(robot_bp)
    app.register_blueprint(camera_bp)
    app.register_blueprint(position_bp)
    app.register_blueprint(react_bp)
    
    # Legacy template routes (keep for backwards compatibility)
    @app.route('/legacy')
    def legacy_index():
        return render_template('index.html')
    
    @app.route('/legacy/positions')
    def legacy_positions_page():
        return render_template('positions.html')
    
    @app.route('/legacy/command-center')
    def legacy_command_center_page():
        return render_template('command_center.html')
    
    # SocketIO event handlers
    @socketio.on('connect')
    def handle_connect():
        emit('status_update', robot_controller.get_current_status())
    
    @socketio.on('request_status')
    def handle_status_request():
        emit('status_update', robot_controller.get_current_status())
    
    return app, socketio

def main():
    """Main entry point"""
    print("Starting MyCobot320 Web Controller...")
    
    # Load saved positions on startup
    print(f"Loaded {position_service.get_position_count()} saved positions")
    
    app, socketio = create_app()
    
    print(f"Server starting on {HOST}:{PORT}")
    socketio.run(app, host=HOST, port=PORT, debug=DEBUG, allow_unsafe_werkzeug=True)

if __name__ == '__main__':
    main()