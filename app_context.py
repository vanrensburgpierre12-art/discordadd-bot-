"""
Application context module to avoid circular imports.
This module provides the Flask app instance and database context
that can be imported by other modules without creating circular dependencies.
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

# Create Flask app instance
app = Flask(__name__)
app.config['SECRET_KEY'] = Config.FLASK_SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = Config.DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

def get_app_context():
    """Get the Flask application context"""
    return app.app_context()

def init_database():
    """Initialize the database with the app context"""
    with app.app_context():
        from database import init_db
        init_db()