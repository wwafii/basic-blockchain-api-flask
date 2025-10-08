# app.py

import sys
from flask import Flask

# Import Blueprint from api/routes.py
from api.routes import api_bp 

def create_app():
    """Application factory function to create a Flask instance."""
    app = Flask(__name__)
    
    # Register the API Blueprint
    app.register_blueprint(api_bp)
    
    return app

if __name__ == '__main__':
    # Ensure the port is provided as an argument
    if len(sys.argv) < 2:
        print("Usage: python app.py <port>")
        sys.exit(1)

    # Create the application
    app = create_app()
    
    port = int(sys.argv[1])
    # Run the application
    app.run(host='0.0.0.0', port=port)