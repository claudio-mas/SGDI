"""
Workflow and approval blueprint
"""
from flask import Blueprint

workflow_bp = Blueprint('workflows', __name__)

from app.workflows import routes
