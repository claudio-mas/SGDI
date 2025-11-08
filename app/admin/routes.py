"""
Administration routes
"""
from flask import render_template
from app.admin import admin_bp


@admin_bp.route('/dashboard')
def dashboard():
    """Admin dashboard"""
    return "Admin dashboard - To be implemented"


@admin_bp.route('/users')
def users():
    """User management"""
    return "User management - To be implemented"


@admin_bp.route('/settings')
def settings():
    """System settings"""
    return "System settings - To be implemented"


@admin_bp.route('/reports')
def reports():
    """Reports"""
    return "Reports - To be implemented"
