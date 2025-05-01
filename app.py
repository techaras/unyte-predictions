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
    
    # Custom Jinja filter for number formatting
    @app.template_filter('format_number')
    def format_number(value):
        """Format numbers with commas for thousands separator."""
        try:
            # Handle None or empty values
            if value is None or value == '':
                return '0'
            
            # Convert to integer and format with commas
            return "{:,}".format(int(float(value)))
        except (ValueError, TypeError):
            return str(value)
    
    return app

# Add this line - create a global app instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=DEBUG)