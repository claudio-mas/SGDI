"""
WSGI entry point for production deployment
"""
import os
from app import create_app

# Create application instance
# Use FLASK_ENV environment variable to determine configuration
# Defaults to 'production' for safety
app = create_app(os.getenv('FLASK_ENV', 'production'))

if __name__ == '__main__':
    # This block is only used for development/testing
    # In production, Gunicorn will import the 'app' object directly
    app.run()
