"""
Authentication routes
"""
from flask import render_template
from app.auth import auth_bp


@auth_bp.route('/login')
def login():
    """Login page"""
    return "Login page - To be implemented"


@auth_bp.route('/logout')
def logout():
    """Logout route"""
    return "Logout - To be implemented"


@auth_bp.route('/register')
def register():
    """Registration page"""
    return "Register page - To be implemented"


@auth_bp.route('/reset-password')
def reset_password():
    """Password reset page"""
    return "Password reset - To be implemented"
