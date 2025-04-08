from flask import Flask
from config import DEBUG, SECRET_KEY
from routes.main_routes import main
from routes.impact_routes import impact

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.secret_key = SECRET_KEY
    
    # Register blueprints
    app.register_blueprint(main)
    app.register_blueprint(impact)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=DEBUG)