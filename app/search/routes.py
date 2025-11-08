"""
Search routes
"""
from flask import render_template
from app.search import search_bp


@search_bp.route('/')
def search():
    """Search page"""
    return "Search - To be implemented"


@search_bp.route('/advanced')
def advanced_search():
    """Advanced search page"""
    return "Advanced search - To be implemented"


@search_bp.route('/suggestions')
def suggestions():
    """Search suggestions"""
    return "Suggestions - To be implemented"
