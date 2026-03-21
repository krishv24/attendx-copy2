# app/__init__.py - Application factory function that sets up Flask
import os
from flask import Flask, redirect, url_for, request
from config import Config

def create_app(config_class=Config):
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(config_class)

    from app.extensions import db, migrate, login_manager
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Register blueprints
    from app.auth.routes import auth as auth_bp
    from app.admin.routes import admin as admin_bp
    from app.student.routes import student as student_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(student_bp, url_prefix='/student')

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    # Redirect to setup if API key is missing
    @app.before_request
    def check_setup():
        if request.endpoint and ('auth.' in request.endpoint or 'static' in request.endpoint):
            return
            
        try:
            from app.models import Config as DBConfig
            api_key = DBConfig.query.filter_by(key='gemini_api_key').first()
            if not api_key or not api_key.value:
                return redirect(url_for('auth.setup_key'))
        except Exception:
            pass # DB not init yet

    @app.route('/')
    def index():
        from flask_login import current_user
        if current_user.is_authenticated:
            if current_user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('student.dashboard'))
        return redirect(url_for('auth.login'))

    return app
