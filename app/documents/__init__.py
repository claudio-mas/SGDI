"""
Document management blueprint
"""
from flask import Blueprint

document_bp = Blueprint('documents', __name__)

from app.documents import routes
