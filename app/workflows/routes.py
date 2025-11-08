"""
Workflow routes
"""
from flask import render_template
from app.workflows import workflow_bp


@workflow_bp.route('/')
def list_workflows():
    """List workflows"""
    return "Workflow list - To be implemented"


@workflow_bp.route('/<int:id>/approve')
def approve(id):
    """Approve document"""
    return f"Approve workflow {id} - To be implemented"


@workflow_bp.route('/<int:id>/reject')
def reject(id):
    """Reject document"""
    return f"Reject workflow {id} - To be implemented"
