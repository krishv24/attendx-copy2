# app/__init__.py - Application factory function that sets up Flask
import os
from flask import Flask, redirect, url_for, request
from config import Config


def create_app(config_class=Config):
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object(config_class)

    from app.extensions import db, login_manager

    login_manager.init_app(app)

    # Register blueprints
    from app.auth.routes import auth as auth_bp
    from app.admin.routes import admin as admin_bp
    from app.student.routes import student as student_bp
    from app.teacher.routes import teacher as teacher_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(student_bp, url_prefix="/student")
    app.register_blueprint(teacher_bp, url_prefix="/teacher")

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User

        user_doc = db.collection("users").document(str(user_id)).get()
        if user_doc.exists:
            return User.from_dict(user_doc.to_dict())
        return None

    # Redirect to setup if API key is missing
    @app.before_request
    def check_setup():
        if request.endpoint and (
            "auth." in request.endpoint or "static" in request.endpoint
        ):
            return

        try:
            import os

            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                return redirect(url_for("auth.setup_key"))
        except Exception:
            pass  # DB not init yet

    @app.route("/")
    def index():
        from flask import render_template

        return render_template("landing.html")

    return app
