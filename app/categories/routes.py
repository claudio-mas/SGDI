"""
Category management routes
"""
from flask import render_template
from app.categories import category_bp


@category_bp.route('/')
def list_categories():
    """List categories"""
    return "Category list - To be implemented"


@category_bp.route('/<int:id>')
def view_category(id):
    """View category details"""
    return f"View category {id} - To be implemented"
