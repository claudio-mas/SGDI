"""
Category and folder management blueprint
"""
from flask import Blueprint

category_bp = Blueprint('categories', __name__)

from app.categories import routes
